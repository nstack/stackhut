pkgbuild --root root --identifier com.stackhut.toolkit --version 0.6.0 --ownership recommended pkg1/output.pkg  

<?xml version="1.0" encoding="utf-8" standalone="no"?>
<installer-gui-script minSpecVersion="1">
    <title>StackHut Toolkit</title>
    <organization>com.stackhut</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="true" rootVolumeOnly="true" />
    <!-- Define documents displayed at various steps -->
    <welcome    file="welcome.html"    mime-type="text/html" />
    <license    file="license.html"    mime-type="text/html" />
    <conclusion file="conclusion.html" mime-type="text/html" />
    <!-- List all component packages -->
    <pkg-ref id="com.stackhut.toolkit"
             version="0.6.0"
             auth="root">output.pkg</pkg-ref>
    <!-- List them again here. They can now be organized
         as a hierarchy if you want. -->
    <choices-outline>
        <line choice="com.stackhut.toolkit"/>
    </choices-outline>
    <!-- Define each choice above -->
    <choice
        id="com.stackhut.toolkit"
        visible="false"
        title="StackHut CLI Toolkit"
        description="CLI to develope, test, and deploy StackHut services"
        start_selected="true">
      <pkg-ref id="com.stackhut.toolkit"/>
    </choice>
</installer-gui-script>



productbuild --distribution distribution.xml --resources resources --package-path pkg1 --version 0.6.0 stackhut-toolkit.pkg

