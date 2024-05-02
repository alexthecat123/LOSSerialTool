##########################################################################################
# LOSSerialTool                                                                          #
# A tool for bypassing Lisa serialization by hard-coding fixed serial numbers into LOS.  #
# It can also handle deserialization of disks, as well as changing the bozo bits.        #
# You can view the serialization status of images without modifying anything too!        #
# By: Alex Anderson-McLeod                                                               #
# May 2, 2024                                                                         #
##########################################################################################

import os
import argparse

class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


# The hex of LOS's original serial number routine.
originalRoutine = bytes.fromhex('48E70F164E54FF00227C00FE800045EF00042EBC000000077C117202207C00FCF8014242427900FCE018427900FCE01A03106708524266F87E064E754C9100FF489200FF508A508A4E714E71700853975FC8FFFE6EE62EBC00000007303C00AB51C8FFFE4C9100FF489200FF508A508A4E714E71700853975FC8FFFE6EE67C137E00427900FCE018264A4DEF00042A4EDBFC000000707C146100007A4A47660000627C15610000B87C162C4DDBFC00000070610000604A47660000487C176100009E3C3C001841EF0004610000B44A47663041EF0004D1FC000000EC760274007000C0FC000A1418D04251CBFFF676047200C2FC000A1418D24251CBFFF64840300132074E5C4CDF68F04CDF0700228034814ED074024240361EE34B640A610000224A4466F26030321EE349E3500C0000FF670C6100000C4A4466EC6000001A4E75BBCE620A5342670A9DFC0000007078014E7542444E753E3C00044E75343C000C76044240BBCE62049CFC0070321EE349E350534366EE16C0534266E44E75D1FC00000070D1FC00000070424010280014343C0064C0C2424316280015343C000AC6C2D043424316280016D0432248343C001442411619D243534266F816280017D243B04167043E3C00054E75')

# My patched serial number routine, split into two pieces so that the actual hard-coded serial number can be put in the middle.
patchPreSN = bytes.fromhex('48E70F16600000F4227C00FE800045EF00042EBC000000077C117202207C00FCF8014242427900FCE018427900FCE01A03106708524266F87E064E754C9100FF489200FF508A508A4E714E71700853975FC8FFFE6EE62EBC00000007303C00AB51C8FFFE4C9100FF489200FF508A508A4E714E71700853975FC8FFFE6EE67C137E00427900FCE018264A4DEF00042A4EDBFC000000707C146100007A4A47660000627C15610000B87C162C4DDBFC00000070610000604A47660000487C176100009E3C3C001841EF0004610000B44A47663041EF0004D1FC000000EC760274007000C0FC000A1418D04251CBFFF676047200C2FC000A1418D2424287203C00')
patchPostSN = bytes.fromhex('32074E714CDF68F04CDF0700228034814ED074024240361EE34B640A610000224A4466F26030321EE349E3500C0000FF670C6100000C4A4466EC6000001A4E75BBCE620A5342670A9DFC0000007078014E7542444E753E3C00044E75343C000C76044240BBCE62049CFC0070321EE349E350534366EE16C0534266E44E75D1FC00000070D1FC00000070424010280014343C0064C0C2424316280015343C000AC6C2D043424316280016D0432248343C001442411619D243534266F816280017D243B04167043E3C00054E75')

# Strings that are used when searching for serialization info on different types of LOS disks.
toolString = bytes('}OBJ', 'ascii')
toolStringLowerCase = bytes('}obj', 'ascii')
toolStringShort = bytes('{T', 'ascii')
toolStringShortLowerCase = bytes('{t', 'ascii')
officeString = bytes('Office System 1', 'ascii')
officeOther = bytes('Office System ', 'ascii')
lisaGuide = bytes('LisaGuide', 'ascii')

index = 0
prevIndex = 0
lowerCaseIndex = 0
counter = 0
newContents = 0
oldSerial = 0
toolNumber = 0
oldBozo = True
isTool = False
isOfficeSystem = False
isOtherOffice = False

# Saves the patched data back to the file once we're done.
def saveFile(filename):
    with open(filename, 'wb') as image:
        image.write(newContents)

# Sets up argparse with all our command line arguments.
def parse_arguments():
    parser = argparse.ArgumentParser(description="A program that does pretty much everything you could possibly imagine when it comes to Lisa disk image serialization!", allow_abbrev=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-patch', metavar='serialNumber', type=validate_positive_int, help='Patch a set of disk images to always report a fixed serial number. serialNumber must be between 0 and 16,777,215, inclusive.')
    group.add_argument('-unpatch', action='store_true', help='Unpatch a previously-patched set of disk images.')
    parser.add_argument('-deserialize', action='store_true', help='Deserialize a set of disk images.')
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('-setbozo', action='store_true', help='Set the bozo bits in all the disk images, enabling serialization.')
    group2.add_argument('-clearbozo', action='store_true', help='Clear the bozo bits in all the disk images, disabling serialization.')

    args = parser.parse_args()

    if args.patch is not None and args.unpatch:
        parser.error("Options -patch and -unpatch can't be used together!")

    if args.setbozo and args.clearbozo:
        parser.error("Options -setbozo and -clearbozo can't be used together!")

    return args

# Checks that the serial number argument is an int in the proper range (up to 24 bits) and raises an exception if not.
def validate_positive_int(value):
    ivalue = int(value)
    if ivalue < 0 or ivalue > 16777215:
        raise argparse.ArgumentTypeError(f"serialNumber {value} is out of bounds! Allowed range is 0 - 16,777,215.")
    return ivalue

# Parse the arguments.
args = parse_arguments()

# And then set our patch and serial number variables depending on what the user specified.
if args.patch == None:
    patch = False
    serial = 0
else:
    patch = True
    serial = args.patch

# The other arguments are easier; just set our variables to exactly what was provided by the user.
unpatch = args.unpatch
removeSerial = args.deserialize
removeBozo = args.clearbozo
addBozo = args.setbozo

# If the user elected to patch their images with a fixed serial number, we'll end up here.
if patch:
    # Iterate through all files in the current directory.
    for fname in os.listdir('.'):
        if os.path.isfile(fname):
            # And only act on files with the extension .dc42 or .image.
            if(fname.split('.')[len(fname.split('.')) - 1] == 'dc42' or fname.split(".")[len(fname.split('.')) - 1] == 'image'):
                with open(fname, 'rb') as image: # Open the disk image.
                    contents = image.read() # And read the contents.
                    index = 0
                    counter = 0
                    newContents = contents # Make a copy of the contents since the original is read-only.
                    while True:
                        # Look for the original SN routine in our file, using the index from our previous iteration as the start point.
                        index = newContents.find(originalRoutine, index)
                        # If there aren't any more instances of the routine in the file, we're done.
                        if index == -1:
                            break
                        # If there are, replace the routine with pre-SN patch, followed by the 24-bit SN from the user, and then the post-SN patch code.
                        newContents = newContents[:index] + patchPreSN + serial.to_bytes(3, byteorder='big') + patchPostSN + newContents[index + len(originalRoutine):]
                        # Increment the index to right after what we just patched.
                        index += len(originalRoutine)
                        counter += 1 # And increment our "patched instance" counter.
                # If the counter is 0 after all this, we found no instances of the original SN routine. This could either mean that it's not an LOS disk, or that it's already been patched.
                if counter == 0:
                    # So open the file again.
                    with open(fname, 'rb') as image:
                        contents = image.read()
                        index = 0
                        # And check to see if there's a patched routine that's been patched with the exact SN that we're trying to patch with now.
                        index = contents.find(patchPreSN + serial.to_bytes(3, byteorder='big') + patchPostSN)
                    if index != -1: # If we end up finding such a routine, then print a message saying that it's already been patched.
                        print(Color.BLUE + fname + ': ' + Color.GREEN + 'Already patched with serial number ' + str(serial) + '!' + Color.END)
                    # If that still isn't the case, then there are two options left: Either it's not an LOS disk, or it's already been patched, but with a different SN.
                    else:
                        # So open the file once again.
                        with open(fname, 'rb') as image:
                            contents = image.read()
                            index = 0
                            counter = 0
                            newContents = contents
                            while True:
                                # And look for each instance of the patched SN routine, just as we did with the original SN routine earlier.
                                index = newContents.find(patchPreSN, index)
                                if index == -1:
                                    break
                                # If we end up here, then the index was non-negative and thus a patched routine was found.
                                oldSerial = newContents[(index + 255):(index + 258)] # So save whatever serial number the disk was previously patched with.
                                # And then overwrite the old patch with our new patch. Really, we could just overwrite the SN part, but this is easier.
                                newContents = newContents[:index] + patchPreSN + serial.to_bytes(3, byteorder='big') + patchPostSN + newContents[index + len(originalRoutine):]
                                index += len(originalRoutine)
                                counter += 1
                        # If counter is zero, then we didn't find any occurrances of the patched routine either, meaning that this definitely isn't an LOS disk.
                        if counter == 0:
                            # So print a message to that effect.
                            print(Color.BLUE + fname + ': ' + Color.RED + 'ERROR - No instances of a SN routine found. Are you sure this is an LOS disk?' + Color.END)
                        # If counter is nonzero, then we found some patches that need their SNs updated to the new value.
                        else:
                            saveFile(fname) # So save the updates to the file.
                            # And then print a message telling the user how many instances of the routine were updated, what the old serial number was, and what the updated serial number is.
                            print(Color.BLUE + fname + ': ' + Color.GREEN + 'Updated ' + str(counter) + ' instance(s) of pre-existing patch from serial number ' + str(int.from_bytes(oldSerial, 'big')) + ' to serial number ' + str(serial) + '.' + Color.END)
                # This is the else from all the way up in the "patch a disk with an original SN routine" section. So this gets executed if we had an original (unpatched) serial number routine on our disk.
                else:
                    saveFile(fname) # Save our newly-patched file.
                    # And print a message telling the user how many instances of the routine were updated and the SN that they were updated with.
                    print(Color.BLUE + fname + ': ' + Color.GREEN + 'Successfully patched ' + str(counter) + ' instance(s) of original SN routine with serial number ' + str(serial) + '.' + Color.END)

# If the user specified the -u flag to unpatch their previously-patched images, we'll end up here.
if unpatch:
    # Iterate through all files in the current directory.
    for fname in os.listdir('.'):
        if os.path.isfile(fname):
            # And only act on files with the extension .dc42 or .image.
            if(fname.split('.')[len(fname.split('.')) - 1] == 'dc42' or fname.split(".")[len(fname.split('.')) - 1] == 'image'):
                with open(fname, 'rb') as image: # Open the disk image.
                    contents = image.read() # And read the contents.
                    index = 0
                    counter = 0
                    newContents = contents # Make a copy of the contents since the original is read-only.
                    while True:
                        # Look for the patched SN routine in our file, using the index from our previous iteration as the start point.
                        index = newContents.find(patchPreSN, index)
                        # If there aren't any more instances of the routine in the file, we're done.
                        if index == -1:
                            break
                        oldSerial = contents[(index + 255):(index + 258)] # If we found one, retrieve the SN that it's patched with so that we can show the user later.
                        # And then replace the patched routine with the original routine.
                        newContents = newContents[:index] + originalRoutine + newContents[index + len(originalRoutine):]
                        # Increment the index to right after what we just replaced.
                        index += len(originalRoutine)
                        counter += 1 # And increment our "replaced instance" counter.
                # If the counter is 0 after all this, we found no instances of the patched SN routine. This could either mean that it's not an LOS disk, or that it's already an original disk.
                if counter == 0:
                    # So open the file again.
                    with open(fname, 'rb') as image:
                        contents = image.read()
                        index = 0
                        # And check to see if there's already an unpatched routine on the disk.
                        index = contents.find(originalRoutine)
                    if index != -1: # If we end up finding such a routine, then print a message saying that it's already an original disk.
                        print(Color.BLUE + fname + ': ' + Color.GREEN + 'Image is already unpatched!' + Color.END)
                    # If we still don't find a routine, then it can't be an LOS disk. So tell the user.
                    else:
                        print(Color.BLUE + fname + ': ' + Color.RED + 'ERROR - No instances of a SN routine found. Are you sure this is an LOS disk?' + Color.END)
                # This is the else from all the way up at the top, where we checked for instances of the patched SN routine. We'll end up here if any were found and replaced with the original routine.
                else:
                    saveFile(fname) # Save our newly-unpatched file.
                    # And print a message telling the user how many instances of the routine were unpatched and the SN of patched routine that was previously there.
                    print(Color.BLUE + fname + ': ' + Color.GREEN + 'Successfully reverted ' + str(counter) + ' instance(s) of patched SN routine, which used serial number ' + str(int.from_bytes(oldSerial, 'big')) + ', to the original routine.' + Color.END)

# If the user chose to do a patching operation, as well as doing a serialization or bozoization operation, put an empty line between them for clarity.
if (patch or unpatch) and (removeSerial or removeBozo or addBozo):
    print()

# If the user elected to deserialize, bozoize, or debozoize their image, we'll end up here.
if removeBozo or removeSerial or addBozo:
    # Go through all .dc42 and .image files in the directory.
    for fname in os.listdir('.'):
        if os.path.isfile(fname):
            if(fname.split('.')[len(fname.split('.')) - 1] == 'dc42' or fname.split(".")[len(fname.split('.')) - 1] == 'image'):
                # Open each file.
                with open(fname, 'rb') as image:
                    contents = image.read() # Read its contents.
                    newContents = contents
                    index = 0
                    prevIndex = -1 # We're going to search for the last occurrance of something, so this will hold that final occurrance after index starts returning -1.
                    lowerCaseIndex = 0 # We need to search in upper and lowercase, so this will store the index for lowercase.
                    # Search until no more occurrances are found.
                    while True:
                        # Look for the next occurrance of the lowercase tool string '}obj' that comes before serialization info on a tool disk.
                        # But only look up to index 0xA000. Any occurrances after that aren't related to serialization info.
                        index = newContents.find(toolStringLowerCase, index)
                        # If there are no more to find, break.
                        if index == -1 or index > 0xA000:
                            break
                        # If we found one, put its location in prevIndex to prep for the next iteration.
                        prevIndex = index
                        # And move the index past the tool string we just found.
                        index += len(toolStringLowerCase)
                    # Once we're found the last occurrance before 0xA000, put its index in the lowerCaseIndex.
                    lowerCaseIndex = prevIndex
                    # Reset our index and prevIndex to prep for searching uppercase.
                    index = 0
                    prevIndex = -1
                    # Do the same thing again, but search for '}OBJ' this time. Different tool disks use different cases here.
                    # Once again, only search up to 0xA000.
                    while True:
                        index = newContents.find(toolString, index)
                        if index == -1 or index > 0xA000:
                            break
                        prevIndex = index
                        index += len(toolString)
                    # Now make sure that at least one of these indices is positive. If neither is positive, then we didn't find either tool string, so it's probably not a tool disk.
                    if lowerCaseIndex > -1 or prevIndex > -1:
                        # Store whichever index is larger, the lower or uppercase one, in index. We need to do this because only the final occurrance of this tool string is the one with the serialization info.
                        if lowerCaseIndex > prevIndex:
                            index = lowerCaseIndex
                        else:
                            index = prevIndex
                        # We're pretty sure it's a tool now, so set isTool to true.
                        isTool = True
                        # And decrement the index by 15 so that we can find the start of the tool number.
                        # The full tool number is {TX}obj, where X is a number from 0 to something really big, so we were just searching for the rear end of this.
                        # Since we don't know the size of the number, we can now just decrement the index by 15 and search for '{T' to see where the string starts.
                        # The serial number is indexed from the start of the tool number, which is why we need to know where it is!
                        index -= 15
                        # So find this new starting index.
                        # Annoyingly enough, the "T" in the tool number can be uppercase or lowercase, so search for both.
                        # And then pick whichever index is smaller, because the smaller index will be the one that's closer to where we're searching and thus the one we want.
                        lowerCaseIndex = contents.find(toolStringShortLowerCase, index)
                        index = contents.find(toolStringShort, index)
                        if((lowerCaseIndex < index and lowerCaseIndex > -1) or index == -1):
                            index = lowerCaseIndex
                        # And extract the 4-byte serial number that's located 65 bytes ahead of the tool string.
                        oldSerial = newContents[(index + 65):(index + 69)]
                        # Now grab the tool number. It's the number that starts right after "T" and ends right before "}".
                        # Just grab the 20 bytes after the "T" and then cut it off at the "}" using the partition function and save that as a string.
                        toolNumber = str((contents[(index + 2):(index + 22)]), 'ascii', errors='ignore').partition("}")[0]
                        # If the user wants to deserialize, replace the serial with all 0's.
                        if removeSerial:
                            newContents = newContents[:index + 65] + bytes('\x00\x00\x00\x00', 'ascii') + newContents[(index + 69):]
                        # The bozo bits are 71 bytes ahead of the tool string, so save their state too for future use. A in the first or both bytes means it's off and ones in both means it's on.
                        if(newContents[index + 71] == 0x00):
                            oldBozo = False
                        elif(newContents[index + 71] == 0x01 and newContents[index + 72] == 0x01):
                            oldBozo = True
                        else:
                            oldBozo = False
                        # If the user wants to clear the bozo bits, set them to 0.
                        if removeBozo:
                            newContents = newContents[:(index + 71)] + bytes('\x00', 'ascii') + newContents[(index + 72):]
                        # And if they want to set them, then set them to 1.
                        if addBozo:
                            newContents = newContents[:(index + 71)] + bytes('\x01\x01', 'ascii') + newContents[(index + 73):]
                    # If neither of the indices from earlier were positive, then this isn't a tool disk.
                    else:
                        isTool = False
                    # It's also not a tool disk if it has any of the strings "Office System 1" through "Office System 5" anywhere in it.
                    # In that case, it's an OS installer disk. Some of the OS installers have tool strings that will confuse the above code, which is why we need this check!
                    if contents.find(officeOther + bytes('1', 'ascii')) > -1 or contents.find(officeOther + bytes('2', 'ascii')) > -1 or contents.find(officeOther + bytes('3', 'ascii')) > -1 or contents.find(officeOther + bytes('4', 'ascii')) > -1 or contents.find(officeOther + bytes('5', 'ascii')) > -1:
                        isTool = False
                # If it is in fact a tool disk, save any changes we made and print the appropriate messages out to the user.
                if isTool:
                    print(Color.BLUE + fname + ': ' + Color.END, end='')
                    # A special case of a tool disk that doesn't have valid serialization info is the LisaWrite 2 disk.
                    # It's just the dictionary, so check if another tool string follows soon (within 130 bytes) after the last one we found.
                    # If so, then it's definitely the LisaWrite 2 disk, so just tell the user and don't try to save any serialization changes to disk.
                    # Normal disks normally have several hunder bytes in between tool strings.
                    # Note that these tool strings that come after don't end in }obj since we would've found them already as the last string if they did!
                    if contents.find(toolStringShort, index + len(toolStringShort)) - index < 130:
                        print(Color.GREEN + 'There are no serialization features on the LisaWrite 2 (tool #' + toolNumber + ') disk, so nothing to do here.' + Color.END, end='')
                    else:
                        if int.from_bytes(oldSerial, 'big') == 0 and removeSerial:
                            print(Color.GREEN + 'Tool #' + toolNumber + ' already deserialized! ' + Color.END, end='')
                        elif int.from_bytes(oldSerial, 'big') > 0 and removeSerial:
                            saveFile(fname)
                            print(Color.GREEN + 'Tool #' + toolNumber + ' deserialized; previously serialized with SN ' + str(int.from_bytes(oldSerial, 'big')) + '. ' + Color.END, end='')
                        if addBozo and oldBozo == True:
                            print(Color.GREEN + 'Tool #' + toolNumber + "'s bozo bits already set, so nothing to do here!" + Color.END, end='')
                        elif addBozo:
                            saveFile(fname)
                            print(Color.GREEN + 'Tool #' + toolNumber + "'s bozo bits set!" + Color.END, end='')
                        if removeBozo and oldBozo == False:
                            print(Color.GREEN + 'Tool #' + toolNumber + "'s bozo bits already cleared, so nothing to do here!" + Color.END, end='')
                        elif removeBozo:
                            saveFile(fname)
                            print(Color.GREEN + 'Tool #' + toolNumber + "'s bozo bits cleared!" + Color.END, end='')
                    print()
                # If it's not a tool disk, then it's either an OS installer or a non-LOS disk.
                else:
                    # Reopen the image and read it into a variable.
                    with open(fname, 'rb') as image:
                        contents = image.read()
                        newContents = contents
                        index = 0
                        # Search for strings in the file.
                        while True:
                            # Look for the string "Office System 1".
                            # The Office System 1 disk is the only one of the installers that records the serial number.
                            index = newContents.find(officeString, index)
                            # If we find it between 0x3000 and 0x4000, then break.
                            # We want to ensure that we found the particular occurrance that's between these addresses since that's the only one that contains serialization.
                            if index > 0x3000 and index < 0x4000:
                                break
                            # And if it's not found at all, then also break.
                            if index == -1:
                                break
                            # Otherwise, increment the index by the length of the string to keep looking.
                            index += len(officeString)
                        # If we ended up getting a positive index, then it must be in our 0x3000-0x4000 range.
                        if index > -1:
                            # We know that this is an OS installer disk now.
                            isOfficeSystem = True
                            # Grab the 4-byte serial number, which is 191 bytes ahead of the start of the string.
                            oldSerial = contents[(index + 191):(index + 195)]
                            # If the user wants to deserialize, then replace this number with all 0's.
                            if removeSerial:
                                newContents = newContents[:index + 191] + bytes('\x00\x00\x00\x00', 'ascii') + newContents[(index + 195):]
                        # If the Office System 1 string wasn't found, then it's either another one of the OS installer disks or a non-LOS disk.
                        else:
                            # So set isOfficeSystem to false to say that it's not the Office System 1 disk.
                            isOfficeSystem = False
                            index = 0
                            # And search for the simple string "Office System" between 0x3000 and 0x4000.
                            while True:
                                index = newContents.find(officeOther, index)
                                if index > 0x3000 and index < 0x4000:
                                    break
                                if index == -1:
                                    break
                                index += len(officeOther)
                            # If we found it, then this is one of the other OS installer disks.
                            if index > -1:
                                isOtherOffice = True
                            # And if not, then it's not a tool or OS disk.
                            else:
                                isOtherOffice = False
                    # If it's the Office System 1 disk, save any changes that the user requested to disk and print out the appropriate messages.
                    # The installers have no bozo bits; only a serial number.
                    if isOfficeSystem:
                        print(Color.BLUE + fname + ': ' + Color.END, end='')
                        if int.from_bytes(oldSerial, 'big') == 0 and removeSerial:
                            print(Color.GREEN + 'LOS installer already deserialized! ' + Color.END, end='')
                        elif int.from_bytes(oldSerial, 'big') > 0 and removeSerial:
                            saveFile(fname)
                            print(Color.GREEN + 'LOS install disk 1 deserialized; previously serialized with SN ' + str(int.from_bytes(oldSerial, 'big')) + '. ' + Color.END, end='')
                        if addBozo:
                            print(Color.GREEN + 'No bozo bits to set on LOS install disks.' + Color.END, end='')
                        elif removeBozo:
                            print(Color.GREEN + 'No bozo bits to clear on LOS install disks.'+ Color.END, end='')
                        print()
                    # If it's one of the other installer disks, just print a message saying that there's nothing to do here.
                    elif isOtherOffice:
                        print(Color.BLUE + fname + ': ' + Color.END, end='')
                        if removeSerial and not removeBozo and not addBozo:
                            print(Color.GREEN + 'Nothing to deserialize on LOS install disks 2 and onward.' + Color.END)
                        if removeSerial and removeBozo:
                            print(Color.GREEN + 'Nothing to deserialize or debozoize on LOS install disks 2 and onward.' + Color.END)
                        if removeSerial and addBozo:
                            print(Color.GREEN + 'Nothing to deserialize or bozoize on LOS install disks 2 and onward.' + Color.END)
                        if not removeSerial and addBozo:
                            print(Color.GREEN + 'No bozo bits to set on LOS install disks.' + Color.END)
                        if not removeSerial and removeBozo:
                            print(Color.GREEN + 'No bozo bits to clear on LOS install disks.' + Color.END)
                    # If it's not a tool or OS disk, then it's either LisaGuide or a bad disk.
                    else:
                        # Look for the text "LisaGuide" between indices 0x0000 and 0xE000. If found, it's LisaGuide, so there's nothing to do and we're good.
                        if newContents.find(lisaGuide) < 0xE000 and newContents.find(lisaGuide) > 0x0000:
                            print(Color.BLUE + fname + ': ' + Color.GREEN + 'Nothing to ' + Color.END, end='')
                            if removeSerial and not removeBozo and not addBozo:
                                print(Color.GREEN + 'deserialize ', end='')
                            if removeSerial and removeBozo:
                                print(Color.GREEN + 'deserialize or debozoize ', end='')
                            if removeSerial and addBozo:
                                print(Color.GREEN + 'deserialize or bozoize ', end='')
                            if not removeSerial and removeBozo:
                                print(Color.GREEN + 'debozoize ', end='')
                            if not removeSerial and addBozo:
                                print(Color.GREEN + 'bozize ', end='')
                            print(Color.GREEN + 'on the LisaGuide disk.' + Color.END)
                        # If we don't find that text, then this probably isn't a Lisa install/tool disk.
                        else:
                            print(Color.BLUE + fname + ': ' + Color.RED + 'ERROR - Unable to find anything to ' + Color.END, end='')
                            if removeSerial and not removeBozo and not addBozo:
                                print(Color.RED + 'deserialize.', end='')
                            if removeSerial and removeBozo:
                                print(Color.RED + 'deserialize or debozoize.', end='')
                            if removeSerial and addBozo:
                                print(Color.RED + 'deserialize or bozoize.', end='')
                            if not removeSerial and removeBozo:
                                print(Color.RED + 'debozoize.', end='')
                            if not removeSerial and addBozo:
                                print(Color.RED + 'bozize.', end='')
                            print(' Are you sure this is an LOS intaller or tool disk?' + Color.END)


# If no arguments were given, then we just want to provide info about the disk images in the directory without changing anything.
if not patch and not unpatch and not removeSerial and not removeBozo and not addBozo:
    # Once again, go through all files in the directory that have a .dc42 or .image extension.
    for fname in os.listdir('.'):
        if os.path.isfile(fname):
            if(fname.split('.')[len(fname.split('.')) - 1] == 'dc42' or fname.split(".")[len(fname.split('.')) - 1] == 'image'):
                # Open the file.
                with open(fname, 'rb') as image:
                    # And read its contents.
                    contents = image.read()
                    index = 0
                    # Search for an instance of the original (unpatched) serial number routine.
                    index = contents.find(originalRoutine)
                # If found, tell the user that this disk is not patched.
                if index > -1:
                    print(Color.BLUE + fname + ': ' + Color.YELLOW + 'Image is not patched. ' + Color.END, end='')
                # If no routine is found, then it's either unpatched or not a Lisa disk at all.
                else:
                    # Reopen the image.
                    with open(fname, 'rb') as image:
                        contents = image.read()
                        index = 0
                        # And search for the patch.
                        index = contents.find(patchPreSN)
                        # If found, tell the user it's patched as well as the serial number that we're patched with.
                        if index > -1:
                            oldSerial = contents[(index + 255):(index + 258)]
                            print(Color.BLUE + fname + ': ' + Color.GREEN + 'Patched with SN ' + str(int.from_bytes(oldSerial, 'big')) + '. ' + Color.END, end='')
                        # If not, then it's not an LOS disk, so tell the user.
                        else:
                            print(Color.BLUE + fname + ': ' + Color.RED + 'No instances of a SN routine found. Are you sure this is an LOS disk? ' + Color.END, end='')
                # Now check serialization and bozo bits status.
                with open(fname, 'rb') as image:
                    contents = image.read()
                    index = 0
                    prevIndex = -1
                    lowerCaseIndex = 0
                    # Find the last occurrance of the lowercase tool string, as done earlier in the deserialization section.
                    while True:
                        index = contents.find(toolStringLowerCase, index)
                        if index == -1 or index > 0xA000:
                            break
                        prevIndex = index
                        index += len(toolStringLowerCase)
                    lowerCaseIndex = prevIndex
                    index = 0
                    prevIndex = -1
                    # And do the same for the last occurrance of the uppercase tool string.
                    while True:
                        index = contents.find(toolString, index)
                        if index == -1 or index > 0xA000:
                            break
                        prevIndex = index
                        index += len(toolString)
                    # If either tool string index is positive, then we found a tool string, and this is probably a tool disk.
                    if lowerCaseIndex > -1 or prevIndex > -1:
                        # Pick whichever string index is larger, the lowercase or uppercase one, and put that in index.
                        if lowerCaseIndex > prevIndex:
                            index = lowerCaseIndex
                        else:
                            index = prevIndex
                        # We're pretty sure this is a tool, so set isTool to true.
                        isTool = True
                        # Decrement the index by 15 and search for the start of the tool string. More detail and the rationale for this is given in the deserialization section.
                        index -= 15
                        # Search for both upper and lowercase versions of this string and pick whichever index is smaller.
                        lowerCaseIndex = contents.find(toolStringShortLowerCase, index)
                        index = contents.find(toolStringShort, index)
                        if((lowerCaseIndex < index and lowerCaseIndex > -1) or index == -1):
                            index = lowerCaseIndex
                        # Grab the serial number that the tool has been serialized to.
                        oldSerial = contents[(index + 65):(index + 69)]
                        # As well as the status of the tool's bozo bits.
                        if(contents[index + 71] == 0x00):
                            oldBozo = False
                        elif(contents[index + 71] == 0x01 and contents[index + 72] == 0x01):
                            oldBozo = True
                        else:
                            oldBozo = False
                        # Now grab the tool number. It's the number that starts right after "T" and ends right before "}".
                        # Just grab the 20 bytes after the "T" and then cut it off at the "}" using the partition function and save that as a string.
                        toolNumber = str((contents[(index + 2):(index + 22)]), 'ascii', errors='ignore').partition("}")[0]
                    # If we didn't find any occurrances of the tool string, then this isn't a tool disk.
                    else:
                        isTool = False
                    # If we find any of the strings "Office System 1" through "Office System 5", then it's an OS installer disk.
                    # Some of these disks have tool strings, but they aren't tools, so set isTool accordingly.
                    if contents.find(officeOther + bytes('1', 'ascii')) > -1 or contents.find(officeOther + bytes('2', 'ascii')) > -1 or contents.find(officeOther + bytes('3', 'ascii')) > -1 or contents.find(officeOther + bytes('4', 'ascii')) > -1 or contents.find(officeOther + bytes('5', 'ascii')) > -1:
                        isTool = False
                # If it's a tool, tell the user its serialization and bozoization status.
                if isTool:
                    # Account for the special case for the LisaWrite 2 disk, as described in the deserialization section.
                    if contents.find(toolStringShort, index + len(toolStringShort)) - index < 130:
                        print(Color.GREEN + 'No serialization or bozo bits on the LisaWrite 2 (tool #' + toolNumber + ') disk.' + Color.END, end='')
                    else:
                        if int.from_bytes(oldSerial, 'big') == 0:
                            print(Color.GREEN + 'Tool #' + toolNumber + ' deserialized' + Color.END, end='')
                        elif int.from_bytes(oldSerial, 'big') > 0:
                            print(Color.YELLOW + 'Tool #' + toolNumber + ' serialized with SN ' + str(int.from_bytes(oldSerial, 'big')) + Color.END, end='')
                        if oldBozo == True:
                            print(Color.YELLOW + ' and bozo bits are set.' + Color.END, end='')
                        elif oldBozo == False:
                            print(Color.GREEN + ' and bozo bits are cleared.' + Color.END, end='')
                # If it's not a tool, then it might be an OS installer. Or maybe it's neither.
                else:
                    # Reopen the image.
                    with open(fname, 'rb') as image:
                        contents = image.read()
                        index = 0
                        # And search for the string "Office System 1", as described in the deserialization section.
                        # Only the first installer disk is serialized.
                        while True:
                            index = contents.find(officeString, index)
                            if index > 0x3000 and index < 0x4000:
                                break
                            if index == -1:
                                break
                            index += len(officeString)
                        # If we find this, then it's definitely an installer disk, so grab the serial number.
                        if index > -1:
                            isOfficeSystem = True
                            oldSerial = contents[(index + 191):(index + 195)]
                        # If not, then it might be one of the other four install disks.
                        else:
                            isOfficeSystem = False
                            index = 0
                            # So check for the simple string "Office System".
                            while True:
                                index = contents.find(officeOther, index)
                                if index > 0x3000 and index < 0x4000:
                                    break
                                if index == -1:
                                    break
                                index += len(officeOther)
                            # If we find it in the desired range, then it's one of the other installer disks.
                            if index > -1:
                                isOtherOffice = True
                            # If not, then this isn't a tool or OS install disk.
                            else:
                                isOtherOffice = False
                    # If it's install disk 1, then give the user the appropriate serialization info.
                    if isOfficeSystem:
                        if int.from_bytes(oldSerial, 'big') == 0:
                            print(Color.GREEN + 'LOS install is deserialized. ' + Color.END, end='')
                        elif int.from_bytes(oldSerial, 'big') > 0:
                            print(Color.YELLOW + 'Serialized with SN ' + str(int.from_bytes(oldSerial, 'big')) + '. ' + Color.END, end='')
                        print(Color.GREEN + 'No bozo bits on LOS install disk 1.' + Color.END, end='')
                    # If it's one of the other install disks, tell the user that there's no info to give.
                    elif isOtherOffice:
                        print(Color.GREEN + 'No serialization or bozo bits on LOS install disks 2 and onward.' + Color.END, end='')
                    # If it's not an OS installer or a tool, it's either LisaGuide or something else random.
                    else:
                        # Look for the "LisaGuide" text between 0x0000 and 0xE000. If so, it's LisaGuide, and there's no serialization or bozo bits to worry about.
                        if contents.find(lisaGuide) < 0xE000 and contents.find(lisaGuide) > 0x0000:
                            print(Color.GREEN + 'No serialization or bozo bits on the LisaGuide disk.' + Color.END, end='')
                        # If not, then this isn't an LOS tool/installer, so tell the user.
                        else:
                            print(Color.RED + 'Unable to find any serialization or bozo bit info. Are you sure this is an LOS installer or tool disk?' + Color.END, end='')
                print()
