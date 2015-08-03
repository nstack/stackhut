# Copyright 2015 StackHut Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Module handles storage backends for running locally and on the cloud
"""
import abc
import shutil
import redis
import threading
from boto.s3.connection import Key, S3Connection
from utils import *

###################################################################################################
# StackHut IO Handling on local and cloud backends
class ControlListener(threading.Thread):
    """Listener listens for requests on Redis Control channel common to all services"""
    def __init__(self, store, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.store = store
        self.pubsub = store.redis.pubsub()
        self.pubsub.subscribe(['{}-control'.format(store.service_fullname)])
        self.can_quit = True
        self.cv = threading.Condition()

    def run(self):
        # infinite loop on listen channel generator
        for item in self.pubsub.listen():
            log.debug(item)
            if item['type'] == 'message':
                if item['data'] == b"KILL":
                    self.pubsub.unsubscribe()
                    with self.cv:
                        self.cv.wait_for(lambda: self.can_quit)
                        log.debug("Shutting down on KILL request")
                        os._exit(os.EX_OK)
                else:
                    log.error("Got unknown message on control channel - \n\t{}".format(item))
                    os._exit(os.EX_DATAERR)

    # NOTE - this is not thread-safe in case of control msg received 1st, then data msg on blpop
    # channel during shutdown itself - will result in a lost message but unlikely to occur.
    # Solve by putting blpop on another thread and sync between them
    def stop(self):
        with self.cv:
            self.can_quit = False
            self.cv.notify_all()  # this is not needed - as will never run again

class IOStore:
    """A base wrapper wrapper around common IO task state"""
    @abc.abstractmethod
    def get_request(self):
        pass

    @abc.abstractmethod
    def put_response(self, s):
        pass

    def get_file(self, name):
        log.error("Store.get_file called")

    @abc.abstractmethod
    def put_file(self, fname, req_id='', make_public=False):
        pass

    def set_task_id(self, task_id):
        log.debug("Task id is {}".format(task_id))
        self.task_id = task_id

class CloudStore(IOStore):
    """Main storage subsytem for use in prod env"""
    def _get_env(self, k):
        v = os.environ.get(k, None)
        del os.environ[k]
        return v

    def __init__(self, service_fullname):
        self.service_fullname = service_fullname

        # open connection to AWS
        aws_id = self._get_env('AWS_ID')
        aws_key = self._get_env('AWS_KEY')
        self.conn = S3Connection(aws_id, aws_key)
        self.bucket = self.conn.get_bucket(S3_BUCKET)
        log.debug("Connected to AWS S3")

        # open connection to Redis
        redis_url = self._get_env('REDIS_URL')
        self.redis = redis.StrictRedis(host=redis_url, port=6379, db=0, password=None,
                                       socket_timeout=None, connection_pool=None, charset='utf-8',
                                       errors='strict', unix_socket_path=None)
        self.redis.ping()
        log.debug("Connected to Redis")

        # setup control listener on sep thread
        self.control = ControlListener(self, daemon=True)
        self.control.start()

    def get_request(self):
        """Get the request JSON"""
        log.debug("Waiting on queue for service - {}".format(self.service_fullname))
        x = self.redis.blpop(self.service_fullname, 0)[1].decode('utf-8')
        # shutdown control listener
        self.control.stop()
        log.debug("Received message {}".format(x))
        return x

    def put_response(self, s):
        """Save the response JSON"""
        log.debug("Pushing task result")
        self.redis.lpush(self.task_id, s.encode('utf-8'))

    def _create_key(self, name):
        k = Key(self.bucket)
        k.key = '{}/{}'.format(self.task_id, name)
        return k

    # def get_file(self, name):
    #     # k = self._create_key(name)
    #     # s = k.get_contents_as_string(encoding='utf-8')
    #     # log.info("Downloaded {} from S3".format(name))
    #     # return s

    def put_file(self, fname, req_id='', make_public=True):
        """Upload file to S3"""
        log.info("Uploading to S3")
        k = self._create_key(os.path.join(req_id, fname))

        if req_id == '':
            req_fname = fname
        else:
            req_fname = get_req_file(req_id, fname)

        k.set_contents_from_filename(req_fname)

        log.info("Uploaded {} to {} in S3".format(req_fname, k))

        if make_public:
            k.set_acl('public-read')
            k.make_public()
            return k.generate_url(expires_in=0, query_auth=False)
        else:
            return k.key

class LocalStore(IOStore):
    """Mock storage system for local testing"""
    local_store = "run_result"

    def _get_path(self, name):
        return "{}/{}".format(self.local_store, name)

    def __init__(self, request_file, uid_gid=None):
        self.uid_gid = uid_gid
        # delete and recreate local_store
        shutil.rmtree(self.local_store, ignore_errors=True)
        if not os.path.exists(self.local_store):
            os.mkdir(self.local_store)

        # copy any files that should be there into the dir
        shutil.copy(request_file, self.local_store)
        self.request_file = self._get_path(request_file)

    def cleanup(self):
        # change the results owner
        if self.uid_gid is not None:
            sh.chown('-R', self.uid_gid, self.local_store)

    def get_request(self):
        with open(self.request_file, "r") as f:
            x = f.read()
        return x

    def put_response(self, s):
        with open(self._get_path('response.json'), "w") as f:
            f.write(s)

    # def get_file(self, name):
    #     pass

    def put_file(self, fname, req_id='', make_public=True):
        """Put file into a subdir keyed by req_id in local store"""
        if req_id == '':
            req_fname = fname
        else:
            req_fname = get_req_file(req_id, fname)

        local_store_dir = self._get_path(req_id)

        os.mkdir(local_store_dir) if not os.path.exists(local_store_dir) else None
        shutil.copy(req_fname, local_store_dir)
        return os.path.join(local_store_dir, fname)

