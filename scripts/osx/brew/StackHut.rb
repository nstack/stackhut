class StackHut < Formula
  desc "StackHut CLI Tool"
  homepage "https://www.stackhut.com"
  url "http://www.rarlab.com/rar/rarosx-5.2.1.tar.gz"
  sha256 "78f023dc1ba1d95f5c2fb5b90c16f214c8bfd2973bf79d92b8a523d711a57065"

  bottle :unneeded

  def install
    bin.install "rar", "unrar"
    lib.install "default.sfx"
    etc.install "rarfiles.lst"
    doc.install "acknow.txt", "order.htm", "rar.txt", "whatsnew.txt"
  end
end

