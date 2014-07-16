import dbus
import gobject
import commands,os,sys,random
import time

class DeviceAddedListener:
    def __init__(self):
        self.bus = dbus.SystemBus()
        self.hal_manager_obj = self.bus.get_object(
                                              "org.freedesktop.Hal", 
                                              "/org/freedesktop/Hal/Manager")
        self.hal_manager = dbus.Interface(self.hal_manager_obj,
                                          "org.freedesktop.Hal.Manager")
        self.hal_manager.connect_to_signal("DeviceAdded", self._filter)
        self.hal_manager.connect_to_signal("DeviceRemoved", self._removal)
        
    def _filter(self, udi):
        device_obj = self.bus.get_object ("org.freedesktop.Hal", udi)
        device = dbus.Interface(device_obj, "org.freedesktop.Hal.Device")

        if device.QueryCapability("volume"):
            return self.do_something(device)
        
    def _removal(self,udi):

        if self.mounted:
            result = commands.getstatusoutput('sudo umount -f %s' % (self.mount_dir))
            result = commands.getstatusoutput('sudo rm -rf %s' % (self.mount_dir))
            print "Jobs Done."
            self.mounted = False
                    
    def do_something(self, volume):
        """
        sets all the properties of the drive.
        """
        self.device_file = volume.GetProperty("block.device")
        self.label = volume.GetProperty("volume.label")
        self.fstype = volume.GetProperty("volume.fstype")
        self.mounted = volume.GetProperty("volume.is_mounted")
        self.mount_point = volume.GetProperty("volume.mount_point")
        self.uuid = volume.GetProperty("volume.uuid")
        try:
            size = volume.GetProperty("volume.size")
        except:
            size = 0

        print "New storage device detected:"
        print "  device_file: %s" % self.device_file
        print "  UUID: %s"%self.uuid
        print "  label: %s" % self.label
        print "  fstype: %s" % self.fstype
        if self.mounted:
            print "  mount_point: %s" % mount_point
        else:
            print "  not mounted"
        print "  size: %s (%.2fGB)" % (size, float(size) / 1024**3)
        self.mount_dir = "/median/" + self.label
        mkdir = 'sudo mkdir %s' % (self.mount_dir)
        mount = 'sudo mount -U %s %s' % (self.uuid, self.mount_dir)
        print 'Mounting device: %s (%s)' % (self.label, self.mount_dir)
        if not os.path.exists(self.mount_dir):
            result = commands.getstatusoutput(mkdir)
            if result[0] != 0:
                print 'dir creation failed, aborting USB mount...'
                sys.exit(1)
            else:
                result = commands.getstatusoutput(mount)
                self.mounted = True
        else:
            print 'unclean mount directory, please clean up...'
            sys.exit(1)
        cp = "sudo cp ./payload.txt /media/"+self.label+"/payload.txt"
        result = commands.getstatusoutput(cp)
        if result[0] != 0:
           print 'Failed to copy file...'
           sys.exit(1)
        else:
            print "Copied file..."
        result = commands.getstatusoutput('sudo umount -f %s' % (self.mount_dir))
        if result[1] == 'umount: %s: not mounted' % (self.mount_dir):
            commands.getstatusoutput('sudo rm -rf %s' % (self.mount_dir))
        result = commands.getstatusoutput('sudo rm -rf %s' % (self.mount_dir))
        print "Cleaning up..."        

if __name__ == '__main__':
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)
    loop = gobject.MainLoop()
    DeviceAddedListener()
    loop.run()