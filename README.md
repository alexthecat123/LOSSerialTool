# LOSSerialTool
A program that does pretty much everything you could possibly imagine when it comes to Lisa disk serialization!

# Introduction
For anyone who doesn't know, the Lisa Office System actually uses DRM (serialization) in order to prevent you from installing your copy on multiple Lisas. This tool allows you to easily view and modify the serialization attributes on all of your LOS disks. Something somewhat similar already exists buried deep in the tools folder of LisaEm, but this one has some additional features, supports batch operations on a bunch of images at a time, and is a little easier to use in my opinion.

# Fun Technical Stuff
Interestingly enough, the Lisa's DRM doesn't actually apply to the OS itself; it's used on all the tool (AKA application) disks that you use to install your LOS apps after installing the operating system itself. This DRM scheme is known as serialization; whenever you copy an app from a floppy to your Lisa's hard drive for the first time, the Lisa will prompt you that you're about to serialize that disk to your Lisa, and if you choose to proceed, your Lisa's serial number will be written to the object file entry in the disk's Volume Catalog. Now, if you try to use that same "serialized" disk on a different Lisa, the new Lisa will still copy the tool over to your hard drive just fine, but will copy the other Lisa's serial number over along with it. Now, if you try to run the app, the Lisa will read that serial number, notice that it doesn't match the computer's actual serial, and then give you a license error. Before serialization, the serial number field on the disk is just all zeros, so zeroing out this field on a serialized disk ("deserializing" the disk) will return the disk to its virgin state and allow it to be used on other Lisas. But of course, this doesn't remove the Lisa's serialization capabilities; it simply resets the disk for use on a single new Lisa.

Fortunately, there just so happen to be two bytes located a couple words after the serial number string in the Volume Catalog that control the enabling and disabling of serialization as a whole. If both of these bytes are 0x01, then serialization will be enabled. If the first byte or both bytes are zeros, then serialization will be disabled, your Lisa's serial number will never be copied over to the disk, and you can install on as many Lisas as you'd like without having to worry about anything! When Ray Arachelian first discovered this, he referred to them as "bozo bits", so that's what I'm going to go with here too.

Oddly enough, two of the LOS 3 tools have serialization disabled by default: LisaWrite and LisaProject. I have no idea why they chose to clear the bozo bits on those two disks, but you can copy those two tools to as many Lisas as you'd like without issue, right out of the box! LisaWrite Disk 2 (the American Dictionary disk) doesn't have any serialization features to begin with since you need Disk 1 in order to do anything useful with it. LOS 2, on the other hand, has all its apps serialized by default. And certain third-party apps, such as the Videx calendar, have serialization enabled as well.

Although it doesn't actually have serialization, your Lisa's serial number is written LOS Install Disk 1 whenever you install the OS. But nothing is ever done with this, so it's not a huge deal.

A final interesting serialization-related thing: Now that we have access to the LOS source code, I was able to track down the assembly language routine that LOS uses to read the Lisa's serial number out of the VSROM. After some messing around, I was able to patch this routine to force it to return a hard-coded serial number, bypassing the VSROM stuff entirely. Simply patch the routine on the installer floppy disks and your OS will install with a hard-coded serial number of your choosing! This program makes it easy to apply this patch if you'd like.

# Using It!
To use this program, put all your LOS disk images that you want to mess with in the same directory as the python script. This program looks for images with extensions of .dc42 and .image. All command line options are applied to all the disk images in the directory. Run the program by typing `python3 LOSSerialTool.py` followed by any options that you'd like to choose.

For all of the following commands, the output is color-coded for legibility, with the image names appearing in blue, results that are likely to be considered desirable in green, results that might be considered undesirable in yellow, and errors in red.

Despite the fact that some of the following commands don't apply to all LOS disks (for instance, LOS install disk 1 has a serial number but no bozo bits and the LisaWrite 2 disk has neither), they can all be run on any assortment of disks and will simply alert the user if a particular disk was skipped because it was unsuitable for the operation.

## Running Without Options
Running the tool without any options will cause it to print the existing serialization attributes of your disk images without modifying anything. This will show you whether or not the "hard-coded serial number" patch described above is applied, and if so, what serial number is hard-coded, as well as whether or not the disk is serialized (and what serial number it's serialized with if so) and whether or not the bozo bits are set.

## Option: `-h` or `--help`
The help option will display a brief summary of all of the following commands.

## Option: `-patch serialNumber`
This option patches the LOS serial number routine with a hard-coded serial number of your choosing (serialNumber). This number must be between 0 and 16,777,215, inclusive. Note that this must be run with all of the LOS installer disks in the directory; all install disks must be patched in order for LOS to successfully install with the patched serial number. You can patch tool floppies as well (they have the serial number routine too for some reason), but this makes no difference whatsoever. It isn't possible to patch a preexisting LOS installation. This might not seem super useful right now (although it is super cool to be able to change your Lisa's serial number to whatever you'd like), but I'm eventually hoping that an improved version of this feature will allow you to use LOS without having to remove a 16MHz XLerator from your system.

## Option: `-unpatch`
This option reverts disks that were previously patched with the hard-coded serial number routine back to LOS's original serial number routine. Once again, this should be run on all of the LOS installer disks in order to fully revert the patch.

## Option: `-deserialize`
This option deserializes a previously-serialized tool disk, allow the tool/app to be installed on another Lisa. As explained earlier, this doesn't permanently disable serialization; it simply restores the disk to its virgin factory state by clearing the serial number field and the next Lisa you install it on will still serialize the disk with its own serial number.

## Option: `-clearbozo`
This option clears the bozo bits on tool disks, completely disabling serialization and allowing you to install the tools on as many Lisas as you'd like. If the disk that you're clearing the bozo bits on was previously serialized, make sure to use the `-deserialize` option before, simultaneously with, or after using this option.

## Option: `-setbozo`
If you're some sort of psychopath who wants to enable serialization on disks that previously had it disabled, then this option is for you! The only reason I can think of for using it would be to achieve consistency across all LOS 3 tools by turning serialization on for the two that had it off originally, but maybe people will find it useful for serializing other previously unserialized things too!

# Issues and Further Information
I don't currently know of any problems with this program, but please let me know if you find any! And also feel free to contact me if you have any questions. My email address is alexelectronicsguy@gmail.com if you need anything!

# Changelog
5/2/2024 - Initial Release
