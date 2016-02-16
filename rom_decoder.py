# this is a quick hack to unparcel Mac OS 9.x ROM files
# thanks to Gwenole Beauchesne for the SheepShaver code which inspired this
import struct

# translated without thought from Gwenole's C++ code
def decode_lzss(src, size):
	dest = ""
	_dict = ['\x00'] * 0x1000
	run_mask = 0
	dict_idx = 0xfee
	idx = 0
	while True:
		if (run_mask < 0x100):
			# Start new run
			if idx >= size: break
			run_mask = ord(src[idx]) | 0xff00
			idx = idx + 1
		bit = run_mask & 1
		run_mask = run_mask >> 1
		if bit:
			# Verbatim copy
			if idx >= size: break
			c = src[idx]
			idx = idx + 1
			_dict[dict_idx] = c
			dest = dest + c
			dict_idx = (dict_idx + 1) & 0xfff
		else:
			# Copy from dictionary
			if idx >= size: break
			thisidx = ord(src[idx])
			idx = idx + 1
			if idx >= size: break
			cnt = ord(src[idx])
			idx = idx + 1
			thisidx = thisidx | ((cnt << 4) & 0xf00)
			cnt = (cnt & 0xf) + 3
			while cnt:
				cnt = cnt - 1
				c = _dict[thisidx]
				thisidx = (thisidx + 1) & 0xfff
				_dict[dict_idx] = c
				dict_idx = (dict_idx + 1) & 0xfff
				dest = dest + c
	return dest

def read32(f):
        x = f.read(4)
        return struct.unpack(">I", x)[0]
def read16(f):
        x = f.read(2)
        return struct.unpack(">H", x)[0]
def read8(f):
        x = f.read(1)
        return struct.unpack(">B", x)[0]

import sys
f = open(sys.argv[1])
bootinfo = ""
while True:
  c = f.read(1)
  if c == '\x00': break
  bootinfo = bootinfo + c
parcelstrloc = bootinfo.index("constant parcels-offset")
startpos = int(bootinfo[parcelstrloc-7:parcelstrloc], 16)
f.seek(startpos)
assert f.read(4) == "prcl"
f.read(4) # version maybe?
next_parcel_offset = read32(f) # ??
assert read32(f) == next_parcel_offset # ??
f.read(4) # zeros?

while True:
	f.seek(startpos + next_parcel_offset)
	next_parcel_offset = read32(f)
	print "entry type: " + f.read(4)
	data_start = read32(f)
	unk1 = read32(f)
	entry_count = read32(f)
	subentrylength = read32(f)
	assert subentrylength == 0x3c
	entry_name = f.read(0x20).strip('\x00')
	print "entry name: " + entry_name
	entry_typething = f.read(0x20).strip('\x00')
	if entry_typething:
		print "entry extra type: " + entry_typething # ?
	for n in range(entry_count):
		subentrytype = f.read(4)
		print "  subentry type: " + subentrytype
		sunk1 = read16(f)
		sunk2 = read16(f)
		print "      unknowns: " + hex(sunk1) + " " + hex(sunk2)
		compressiontype = f.read(4)
		print "      compression type: " + compressiontype
		uncomp_size = read32(f)
		checksum = read32(f) # ??
		comp_size = read32(f)
		offset = read32(f)
                print "      uncompressed/compressed sizes: " + str(uncomp_size) + " " + str(comp_size)
		name = f.read(0x20).strip('\x00')
		print "      name: " + name
		print "      @ " + hex(startpos + offset)
		oldpos = f.tell()
		filename = entry_name + "_" + subentrytype + "_" + name
		print "      writing to: " + filename
		outputfile = open(filename, "w")
		f.seek(startpos + offset)
		if compressiontype == "lzss":
			data = decode_lzss(f.read(comp_size), comp_size)
			assert len(data) == uncomp_size
		else:
			assert comp_size == uncomp_size
			data = f.read(uncomp_size)
		outputfile.write(data)
		f.seek(oldpos)
