### AnyKernel3 Ramdisk Mod Script
## begonia (Redmi Note 8 Pro / MT6785 Helio G90T) - KernelSU-Next
## base template: osm0sis @ xda-developers

### AnyKernel setup
# global properties
properties() { '
kernel.string=Argon Kernel 4.14.357 + KernelSU-Next legacy (manual hooks)
do.devicecheck=1
do.modules=0
do.systemless=0
do.cleanup=1
do.cleanuponabort=0
device.name1=begonia
device.name2=begoniain
device.name3=Redmi Note 8 Pro
device.name4=
device.name5=
supported.versions=
supported.patchlevels=
supported.vendorpatchlevels=
'; } # end properties

### AnyKernel install
## boot files attributes
boot_attributes() {
set_perm_recursive 0 0 755 644 $RAMDISK/*;
set_perm_recursive 0 0 750 750 $RAMDISK/init* $RAMDISK/sbin;
} # end attributes

# boot shell variables
BLOCK=/dev/block/bootdevice/by-name/boot;
IS_SLOT_DEVICE=0;
RAMDISK_COMPRESSION=auto;
PATCH_VBMETA_FLAG=auto;

# import functions/variables and setup patching - see for reference (DO NOT REMOVE)
. tools/ak3-core.sh;

# Argon Kernel ASCII signature (shown while flashing)
ui_print " ";
ui_print '    _    ____   ____   ___  _   _';
ui_print '   / \  |  _ \ / ___| / _ \| \ | |';
ui_print '  / _ \ | |_) | |  _ | | | |  \| |';
ui_print ' / ___ \|  _ <| |_| | |_| | |\  |';
ui_print '/_/   \_\_| \_\\____|\___/|_| \_|';
ui_print '        A R G O N   K E R N E L';
ui_print '  begonia | MT6785 | Linux 4.14.357';
ui_print '  KernelSU-Next legacy (manual hooks)';
ui_print '  KernelSU-Next manager v3.4.2';
ui_print '  built by @edis22ovner on XDA';
ui_print '  with the help of DeepSeek V4.1 Flash Free';
ui_print " ";

# boot install
dump_boot;
write_boot;
## end boot install

ui_print " ";
ui_print "KernelSU-Next is built into the kernel.";
ui_print "Install the KernelSU-Next manager APK after booting.";
ui_print "Hold Volume Down during boot for KernelSU safe mode.";
