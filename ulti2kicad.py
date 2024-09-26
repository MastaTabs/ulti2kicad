#!/usr/bin/env python3

import sys
import array as arr
import math
# import json

header = """(kicad_pcb (version 20221018) (generator ulti2kicad)

  (general
    (thickness 1.6)
  )

  (paper "{papersize}")
  (layers
    (0 "F.Cu" signal)
    (1 "In1.Cu" power)
    (2 "In2.Cu" power)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )

  (setup
    (pad_to_mask_clearance 0.051)
    (solder_mask_min_width 0.25)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros false)
      (usegerberextensions false)
      (usegerberattributes true)
      (usegerberadvancedattributes true)
      (creategerberjobfile true)
      (dashed_line_dash_ratio 12.000000)
      (dashed_line_gap_ratio 3.000000)
      (svgprecision 4)
      (plotframeref false)
      (viasonmask false)
      (mode 1)
      (useauxorigin false)
      (hpglpennumber 1)
      (hpglpenspeed 20)
      (hpglpendiameter 15.000000)
      (dxfpolygonmode true)
      (dxfimperialunits true)
      (dxfusepcbnewfont true)
      (psnegative false)
      (psa4output false)
      (plotreference true)
      (plotvalue true)
      (plotinvisibletext false)
      (sketchpadsonfab false)
      (subtractmaskfromsilk false)
      (outputformat 1)
      (mirror false)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "")
    )
  )

"""

class Shape:
    def __init__(self,name,reference,lines,pads,arcs,circles):
        self.name = name
        self.reference = reference
        self.lines = lines
        self.pads = pads
        self.arcs = arcs
        self.circles = circles

    def __str__(self):
        return f"KiCadFootprint({self.name}, {self.reference}, Pads: {len(self.pads)})"

class Pad:
    def __init__(self,kind,x,y,w,h,drill_size,layer):
        self.kind = kind
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.drill_size
        self.layer = layer

class SExpression:
    def __init__(self, name, subvalues=None):
        """
        Initialize the S-Expression object.
        
        :param name: The name of the S-Expression (symbol).
        :param subvalues: A list of subvalues which can be key-value pairs, another S-Expression object,
                          or simple strings/integers.
        """
        self.name = name
        self.subvalues = subvalues if subvalues is not None else []

    def add_subvalue(self, key, value):
        """
        Add a key-value pair as a subvalue to the S-Expression.
        
        :param key: The key of the pair.
        :param value: The value of the pair.
        """
        self.subvalues.append((key, value))

    def add_subexpression(self, subexpression):
        """
        Add a subexpression or simple value (string/int) as a subvalue.
        
        :param subexpression: Another S-Expression object or a simple string/int.
        """
        if isinstance(subexpression, (SExpression, str, int, float)):
            self.subvalues.append(subexpression)
        else:
            raise ValueError("Subexpression should be an SExpression, string, or integer")

    def add_arbitrary_subexpression(self, name, *values):
        """
        Add a subexpression with an arbitrary number of values.
        
        :param name: The name of the subexpression.
        :param values: A variable number of values which can be strings, integers, key-value pairs, or S-Expression objects.
        """
        subexpr = SExpression(name)
        for value in values:
            if isinstance(value, tuple):
                # If it's a key-value pair (tuple), add as subvalue
                subexpr.add_subvalue(*value)
            else:
                # Otherwise, add as a simple value or subexpression
                subexpr.add_subexpression(value)
        self.subvalues.append(subexpr)

    def _escape_value(self, value):
        """
        Helper function to escape string values with double quotes.
        
        :param value: The value to escape if it's a string.
        :return: Escaped string or the original value.
        """
        if isinstance(value, str):
            return f'"{value}"'
        return str(value)

    def __str__(self):
        """
        Serialize the S-Expression to a string.
        """
        subvalue_strings = []
        for subvalue in self.subvalues:
            if isinstance(subvalue, SExpression):
                subvalue_strings.append(str(subvalue))
            elif isinstance(subvalue, tuple):
                key, value = subvalue
                subvalue_strings.append(f"({key} {self._escape_value(value)})")
            else:
                # If it's a simple string or integer
                subvalue_strings.append(self._escape_value(subvalue))
        
        subvalues_str = " ".join(subvalue_strings)
        return f"({self.name} {subvalues_str})"

xScale = (1/1.2) * 0.0254
ncount = -1

traceWidth = {}
traceClearance = {}
drillCode = [0] * 256
padT = [{'X1': 0, 'X2': 0, 'Y': 0, 'Radius': 0, 'Clear': 0, 'Horz': 0, 'Vert': 0, 'ThermH': 0, 'ThermV': 0} for x in range(256)]
padI = [{'X1': 0, 'X2': 0, 'Y': 0, 'Radius': 0, 'Clear': 0, 'Horz': 0, 'Vert': 0, 'ThermH': 0, 'ThermV': 0} for x in range(256)]
padB = [{'X1': 0, 'X2': 0, 'Y': 0, 'Radius': 0, 'Clear': 0, 'Horz': 0, 'Vert': 0, 'ThermH': 0, 'ThermV': 0} for x in range(256)]
nets = {}
# shapes = {}
Shapes = {}

# print(drillCode)

layers = ['F.SilkS','F.Cu','B.Cu','In1.Cu','In2.Cu','F.Mask','B.Mask','B.SilkS','B.Fab','Cmts.User','','','']

def v2mm(val):
    return (val/1.2) * 0.0254

def nnameCheck(name, nb):
    name = name[1:]
    if(name == ""):
        name = "SB${}".format(nb)
    
    ch = 0
    while ch != -1:
        ch = name.find('\'')
        if(ch == -1):
            break
        else:
            name[ch] = '/'
    return name

def str_esc(str):
    escaped = str.translate(str.maketrans({"]":  r"\]",
                                          "\\": r"\\",
                                          "^":  r"\^",
                                          "$":  r"\$",
                                          "*":  r"\*",
                                          "\"": r"\""}))
    return escaped

def split_odd(arr):
    result = []
    sublist = []
    for num in arr:
        if num % 2 != 0:
            if sublist:  # Append the current sublist if not empty
                result.append(sublist)
            sublist = [num]  # Start a new sublist with the odd number
        else:
            sublist.append(num)  # Add even numbers to the current sublist
    if sublist:  # Append the last sublist if not empty
        result.append(sublist)
    return result

with open(sys.argv[1], 'r', encoding="cp850") as ddf, open(sys.argv[2], 'w') as kicad:
    for line in ddf:
        if(line[0] == '*'):
            # print(line)
            line = line.strip()
            match line[1]:
                case 'P':
                    # Header
                    # print("Header")
                    line = next(ddf).strip()
                    line = next(ddf).strip()
                    outline = [v2mm(int(i)) for i in line[:-1].split(',')]
                    # print("Outline ", outline)
                    # hstr = "  (gr_rect (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width 0.1) (layer \"Edge.Cuts\"))\n"
                    # kicad.write(hstr.format(x1 = outline[0], y1 = -outline[1], x2 = outline[2], y2 = -outline[3]))
                    if(outline[0]+(-outline[2]) > 260 ):
                        # print(outline[0]+(-outline[2]))
                        header = header.format(papersize='A3')
                    else:
                        # print(outline[0]+(-outline[2]))
                        header = header.format(papersize='A4')
                    kicad.writelines(header)

                case 'S':
                    # print("Shape " + line[2:])
                    shapeStr = ""
                    sName = line[2:]
                    line = next(ddf).strip()
                    lname = [v2mm(int(i)) for i in line.split(' ')]
                    sNRelx = lname[0]
                    sNRely = -lname[1]
                    sNHeight = lname [2]
                    sNRot = lname[3] / 64
                    sNWidth = lname[4]
                    sNThick = lname[5]

                    line = next(ddf).strip()
                    lalias = [v2mm(int(i)) for i in line.split(' ')]
                    sARelx = lalias[0]
                    sARely = -lalias[1]
                    sAHeight = lalias [2]
                    sARot = lalias[3] / 64
                    sAWidth = lalias[4]
                    sAThick = lalias[5]

                    shapeStr = "(footprint \"library:{sname}\" ".format(sname=sName)
                    shapeStr += " (layer \"{fp_layer}\")\n {component}\n"
                    shapeStr += """  (fp_text user \"${REFERENCE}\" (at {snrelx} {snrely} {snrot}) (layer "F.Fab")\n\
                                    (effects (font (size 0.25 0.25) (thickness 0.04)))\n  )\n"""\
                                    .format(REFERENCE=sName,snrelx=sNRelx,snrely=sNRely,snrot=sNRot)

                    line = next(ddf).strip()
                    rthJuncB = float(line)
                    sline = ""
                    while True:
                        line = next(ddf).strip()
                        if ';' == line[0]: break
                        if ';' in line:
                            sline += line[:-1]
                            break
                        else:
                            sline += line
                    
                    #outline lines
                    if len(sline) > 0:
                        parr = [int(i) for i in sline.split(',')]
                        # print("x/y of lines", parr)
                        oddies = split_odd(parr)
                        for p in oddies:
                            for i in range(0, len(p) - 3, 2):
                                sp = p[i:i+2]
                                ep = p[i+2:i+4]
                                if(i == 0): sp[0] = sp[0]-1
                                
                                if(sName == 'BOARD'):
                                    # handle complex board outline
                                    kicad.write("  (gr_line (start {sx:.4f} {sy:.4f}) (end {ex:.4f} {ey:.4f}) (width 0.1) (layer \"Edge.Cuts\"))\n"\
                                                    .format(sx=v2mm(sp[0]),sy=-v2mm(sp[1]),ex=v2mm(ep[0]),ey=-v2mm(ep[1])))
                                else:
                                    shapeStr += "  (fp_line (start {sx} {sy}) (end {ex} {ey}) (layer \"{fp_side}.SilkS\"))\n"\
                                                    .format(sx=v2mm(sp[0]),sy=-v2mm(sp[1]),ex=v2mm(ep[0]),ey=-v2mm(ep[1]),fp_side="{fp_side}")
                                
                    #Pads
                    pads = []
                    bpads = []
                    while True:
                        line = next(ddf).strip()
                        if len(line) > 1:
                            larr = line[:-1].split(',', 5)
                            pcode    = int(larr[0])
                            pcoderot = float(larr[1])/64
                            pcodels  = int(larr[2],16)
                            pcoderelx = v2mm(int(larr[3]))
                            pcoderely = v2mm(int(larr[4]))
                            pname = larr[5]
                            # print("Pad ", pcode, pcoderot, pcodels, pcoderelx, pcoderely, pname)

                            bpx1 = v2mm(padB[pcode]['X1'])
                            bpx2 = v2mm(padB[pcode]['X2'])
                            bpy  = v2mm(padB[pcode]['Y'])
                            bpr  = v2mm(padB[pcode]['Radius'])
                            bpc  = v2mm(padB[pcode]['Clear'])
                            bph  = v2mm(padB[pcode]['Horz'])
                            bpv  = v2mm(padB[pcode]['Vert'])
                            dc  = drillCode[pcode]
                            # print("Pad2 ", pcoderelx, pcoderely, pcodels, bpx1, bpx2, bpy, bpr, bpc, dc)
                            bpx = bpx1 + bpx2

                            tpx1 = v2mm(padT[pcode]['X1'])
                            tpx2 = v2mm(padT[pcode]['X2'])
                            tpy  = v2mm(padT[pcode]['Y'])
                            tpr  = v2mm(padT[pcode]['Radius'])
                            tpc  = v2mm(padT[pcode]['Clear'])
                            tph  = v2mm(padT[pcode]['Horz'])
                            tpv  = v2mm(padT[pcode]['Vert'])
                            dc  = drillCode[pcode]
                            # print("Pad2 ", pcoderelx, pcoderely, pcodels, tpx1, tpx2, tpy, tpr, tpc, dc)
                            tpx = tpx1 + tpx2

                            bpads.append({'code': pcode,
                                           'rot': pcoderot,
                                         'layer': pcodels,
                                          'relx': pcoderelx,
                                          'rely': pcoderely,
                                          'name': pname,
                                            'x1': bpx1,
                                            'x2': bpx2,
                                             'y': bpy,
                                           'rad': bpr,
                                         'clear': bpc,
                                         'width': bpx,
                                        'height': bpy,
                                         'drill': 0})

                            pads.append({ 'code': pcode,
                                           'rot': pcoderot,
                                         'layer': pcodels,
                                          'relx': pcoderelx,
                                          'rely': pcoderely,
                                          'name': pname,
                                            'x1': tpx1,
                                            'x2': tpx2,
                                             'y': tpy,
                                           'rad': tpr,
                                         'clear': tpc,
                                         'width': tpx,
                                        'height': tpy,
                                         'drill': dc})

                        if ';' in line:
                            break
                    #outline arcs and circles
                    while True:
                        line = next(ddf).strip()
                        if len(line) > 1:
                            larr = line[:-1].split(',')
                            ax = v2mm(int(larr[0]))
                            ay = v2mm(int(larr[1]))
                            ar = v2mm(int(larr[2]))
                            arc1 = int(larr[3]) / 64
                            arc2 = int(larr[4]) / 64
                            # print("Arc ", ax,ay,ar, arc1, arc2)

                            arcStart = 360 + arc1
                            if(arcStart > 360): arcStart -= 360
                            arcMid = -(arcStart + (arc2/2))
                            if(arcMid > 360): arcMid -= 360
                            arcEnd = arcStart + arc2
                            if(arcEnd > 360): arcEnd -= 360
                            xArcStart = ar * math.cos(math.pi / 180 * arcStart)
                            yArcStart = ar * math.sin(math.pi / 180 * arcStart)
                            xArcMid   = ar * math.cos(math.pi / 180 * arcMid)
                            yArcMid   = ar * math.sin(math.pi / 180 * arcMid)
                            xArcEnd   = ar * math.cos(math.pi / 180 * arcEnd)
                            yArcEnd   = ar * math.sin(math.pi / 180 * arcEnd)

                            if(arc2 == 360):
                                circstr = "  (fp_circle (center {xc} {yc}) (end {xe} {ye}) (layer \"{fp_side}.SilkS\") (width 0.1))\n"
                                shapeStr += circstr.format(xc = ax, yc = -ay, xe = ax + ar, ye = -ay,fp_side="{fp_side}")
                            else:
                                astr = "  (fp_arc (start {xs:.4f} {ys:.4f}) (mid {xm:.4f} {ym:.4f}) (end {xe:.4f} {ye:.4f}) (width {width:.3f}) (layer \"{fp_side}.SilkS\"))\n"
                                shapeStr += astr.format(xs = ax + xArcStart, ys = -(ay + yArcStart), xm = ax + xArcMid, ym = -(ay - yArcMid), xe = ax + xArcEnd, ye = -(ay + yArcEnd), width = 0.1,fp_side="{fp_side}")

                        if ';' in line:
                            break
                    # shapeStr += ")\n"
                    # kicad.write(shapeStr)
                    # shapes[sName] = shapeStr
                    Shapes[sName] = {'str': shapeStr, 'pads': pads, 'bpads': bpads}
                case 'T':
                    # print("Technology")
                    match line[2]:
                        case 'P':
                            print("padset " + line[4:])
                        case 'T':
                            tl = [int(i) for i in line[4:].split(',')]
                            # print("Trace ", tl)
                            traceWidth[tl[0]] = tl[1]
                            traceClearance[tl[0]] = tl[2]

                        case 'C':
                            print("Drill tolerance " + line[4:])
                        case 'D':
                            dc = [int(i) for i in line[4:].split(',')]
                            # print("Drill Code ", dc)
                            drillCode[dc[0]] = v2mm(dc[1])
                        case '0':
                            pi = [int(i) for i in line[4:].split(',')]
                            # print("Inner Pads ", pi)
                            padI[pi[0]] = {'X1': pi[1], 'X2': pi[2], 'Y': pi[3], 'Radius': pi[4], 'Clear': pi[5], 'Horz': pi[6], 'Vert': pi[7], 'ThermH': pi[8], 'ThermV': pi[9]}
                        case '1':
                            pi = [int(i) for i in line[4:].split(',')]
                            # print("Top Pads ", [int(i) for i in line[4:].split(',')])
                            padT[pi[0]] = {'X1': pi[1], 'X2': pi[2], 'Y': pi[3], 'Radius': pi[4], 'Clear': pi[5], 'Horz': pi[6], 'Vert': pi[7], 'ThermH': pi[8], 'ThermV': pi[9]}
                        case '2':
                            pi = [int(i) for i in line[4:].split(',')]
                            # print("Bottom Pads ", [int(i) for i in line[4:].split(',')])
                            padB[pi[0]] = {'X1': pi[1], 'X2': pi[2], 'Y': pi[3], 'Radius': pi[4], 'Clear': pi[5], 'Horz': pi[6], 'Vert': pi[7], 'ThermH': pi[8], 'ThermV': pi[9]}
                        case 'S':
                            print("Wave solder dir " + line[4:])
                        case _:
                            print("T?" + line)

                case 'N':
                    # print("Net")
                    larr = line[3:-1].split(" ")
                    ncount += 1
                    # print("Net " + larr[0][1:], [int(i) for i in larr[1:]])
                    # nets[ncount] = larr[0][1:]
                    nets[ncount] = larr[0]
                    if(nets[ncount] == 65535):
                        nets[ncount] = 0
                    # if len(larr[0]) > 1:
                    name = nnameCheck(nets[ncount], ncount)
                    kicad.write("  (net {ncount} \"{name}\")\n".format(ncount = ncount, name = name))
                case 'C':
                    # print("Component")
                    carr = line[3:].split(" ")
                    cname = carr[0]
                    calias = carr[1]
                    cshape = carr[2]
                    carr = next(ddf).strip().split(",")
                    cxpos = v2mm(int(carr[0]))
                    cypos = -v2mm(int(carr[1]))
                    crot  = int(carr[2])/64
                    cnxpos = v2mm(int(carr[3]))
                    cnypos = -v2mm(int(carr[4]))
                    cnrot  = int(carr[5])/64
                    cnhght = v2mm(int(carr[6]))
                    cnwdth = v2mm(int(carr[7]))
                    cnthck = v2mm(int(carr[8]))
                    caxpos = int(carr[9])
                    caypos = int(carr[10])
                    carot  = int(carr[11])
                    cahght = int(carr[12])
                    cawdth = int(carr[13])
                    cathck = int(carr[14])
                    carr = next(ddf).strip().split(",")
                    # carr = next(ddf).strip().split(" ")
                    # print("cname ", cname)
                    nline = ""
                    while True:
                        line = next(ddf).strip()
                        if ';' == line[0]: break
                        nline += line + ' '
                        # print(nline)

                    # print("nline ", nline)
                    narr = [i for i in nline.strip().split(" ")]
                    # print(narr)

                    pnpairs = []
                    for i in range(0, len(narr), 2):
                        pair = narr[i:i+2]
                        # print("pair ", pair)
                        # if pair[0] != '': break
                        pair[0] =  int(pair[0])
                        if pair[0] == 65535: pair[0] = 0
                        if pair[1] == 'ffffffff': pair[1] = 0   # thru hole
                        pair[1] = int(pair[1])
                        # pair.append(pair[1])
                        # pair[1] = 0
                        pnpairs.append(pair)
                    
                    # print("pnp", pnpairs)

                    shape = Shapes[cshape]
                    theside = 'B' if pnpairs[0][1] == 2 and pnpairs[-1][1] == 2 else 'F'

                    mir = ""
                    if theside == 'B':
                        crot = crot + 180
                        mir = "(justify mirror)"
                        cnypos = -cnypos


                    fpadd = "(at {locx} {locy} {rot})\n  ".format(locx = cxpos, locy = cypos, rot = crot)
                    shapeStr = shape['str'].format(component = fpadd, fp_layer = layers[pnpairs[0][1]], fp_side = theside)
                    shapeStr += "  (property \"Reference\" \"{name}\" (layer \"{cnl}.SilkS\")(at {cnx} {cny} {cnrot}) (hide no) (effects (font (size {cnsizex} {cnsizey}) (thickness {cnthick})) {mir}))\n"\
                                    .format(name = cname, cnx = cnxpos, cny = cnypos, cnrot = cnrot+crot, cnl = theside, cnsizex = cnhght, cnsizey= cnwdth, cnthick=cnthck/10, mir=mir)

                    if shape['pads'][0]['drill'] == 0:
                        shapeStr += "  (attr smd)\n"
                    else:
                        shapeStr += "  (attr through_hole)\n"

                    # print(cstr)

                    for pidx,pad in enumerate(shape['pads']):
                        # print("pidx ", pidx, len(pnpairs), pad)

                        if pad['layer'] == 0xffffffff: pad['layer'] = 9
                        # if pnpairs[pidx][0] == 65535: 
                        pname = nnameCheck(nets[pnpairs[pidx][0]], pnpairs[pidx][0])

                        centeroffset = pad['x1'] - pad['x2']
                        px = pad['x1'] + pad['x2']

                        if pad['drill'] == 0:
                            if pad['height'] != 0 and pad['width'] != 0:
                                # smd
                                if pad['y'] == 0: pad['y'] = 0.001
                                if pad['rely'] == 0: pad['rely'] = 0.001
                                roundratio = pad['rad'] / pad['y']

                                if centeroffset == 0:
                                    # bottom pads
                                    if pnpairs[pidx][1] == 2:
                                        shapeStr += "  (pad \"{name}\" smd roundrect (net {nnum} \"{nname}\") (at {x} {y} {rot}) (size {w} {h}) (layers \"{layer}\" \"B.Paste\" \"B.Mask\") (roundrect_rratio {rr}))\n"\
                                                        .format(name = pad['name'], x = pad['relx'], y = -pad['rely'], h = pad['height'], w = pad['width'], rot = crot + pad['rot'], layer=layers[pnpairs[pidx][1]], rr=roundratio, nnum = pnpairs[pidx][0], nname=pname)
                                    else:
                                        shapeStr += "  (pad \"{name}\" smd roundrect (net {nnum} \"{nname}\") (at {x} {y} {rot}) (size {w} {h}) (layers \"{layer}\" \"F.Paste\"  \"F.Mask\") (roundrect_rratio {rr}))\n"\
                                                        .format(name = pad['name'], x = pad['relx'], y = -pad['rely'], h = pad['height'], w = pad['width'], rot = crot + pad['rot'], layer=layers[pnpairs[pidx][1]], rr=roundratio, nnum = pnpairs[pidx][0], nname=pname)
                                else:
                                    match pad['rot']:
                                        case 0:
                                            rx = pad['relx'] - centeroffset/2
                                            ry = pad['rely']
                                        case 90:
                                            rx = pad['relx']
                                            ry = pad['rely'] - centeroffset/2
                                        case 180:
                                            rx = pad['relx'] + centeroffset/2
                                            ry = pad['rely']
                                        case 270:
                                            rx = pad['relx']
                                            ry = pad['rely'] + centeroffset/2
                                    # Bottom
                                    if pnpairs[pidx][1] == 2:
                                        shapeStr += "  (pad \"{name}\" smd roundrect (net {nnum} \"{nname}\") (at {x} {y} {rot}) (size {w} {h}) (layers \"{layer}\" \"B.Paste\" \"B.Mask\") (roundrect_rratio {rr}))\n"\
                                                        .format(name = pad['name'], x = rx, y = -ry, h = pad['height'], w = pad['width'], rot = crot + pad['rot'], layer=layers[pnpairs[pidx][1]], rr=roundratio, nnum = pnpairs[pidx][0], nname=pname)
                                    else:
                                        # print("centeroffset ", centeroffset, pad['x1'], pad['x2'])
                                        shapeStr += "  (pad \"{name}\" smd roundrect (net {nnum} \"{nname}\") (at {x} {y} {rot}) (size {w} {h}) (layers \"{layer}\" \"F.Paste\" \"F.Mask\") (roundrect_rratio {rr}))\n"\
                                                        .format(name = pad['name'], x = rx, y = -ry, h = pad['height'], w = pad['width'], rot = crot + pad['rot'], layer=layers[pnpairs[pidx][1]], rr=roundratio, nnum = pnpairs[pidx][0], nname=pname)
                        else:
                            # thruhole
                            roundratio = pad['rad'] / pad['y']
                            if centeroffset == 0 and px == pad['y']:
                                if pad['rad'] < (px/2):
                                    padshape = "rect"
                                else:
                                    padshape = "circle"
                            else:
                                padshape = "roundrect"
                                pcoderely = pcoderely - centeroffset
                            

                            shapeStr += "  (pad \"{name}\" thru_hole {padshape} (net {nnum} \"{nname}\") (at {x} {y} {rot}) (size {h} {w}) (drill {dc}) (layers \"*.Cu\" \"*.Mask\") (roundrect_rratio {rr}))\n"\
                                            .format(name = pad['name'], x = pad['relx'], y = -pad['rely'], h = pad['height'], w = pad['width'], rot = crot + pad['rot'] - 90, layer=layers[pnpairs[pidx][1]], rr=roundratio, dc = pad['drill'], padshape=padshape, nnum = pnpairs[pidx][0], nname=pname)
                            # handle complex Padstack, right now only works if Top pad is smaller than the bottom one
                            if(shape['bpads'][pidx] != pad):
                                # print('pad diff!!')
                                bpad = shape['bpads'][pidx]
                                shapeStr += "  (pad \"{name}\" smd {padshape} (net {nnum} \"{nname}\") (at {x} {y} {rot}) (size {h} {w}) (drill {dc}) (layers \"B.Cu\" \"B.Mask\") (roundrect_rratio {rr}))\n"\
                                                .format(name = bpad['name'], x = bpad['relx'], y = -bpad['rely'], h = bpad['height'], w = bpad['width'], rot = crot + bpad['rot'] - 90, layer=layers[2], rr=roundratio, dc = bpad['drill'], padshape=padshape, nnum = pnpairs[pidx][0], nname=pname)

                    # cstr += shapeStr
                    kicad.write(shapeStr+"\n)\n")
                case 'L':
                    # print("Subrecord")
                    match line[2]:
                        case 'T':
                            # print("Trace")
                            tline = [int(i) for i in line[4:].split(' ')]
                            # print(tline)
                            layer = int(tline[0])
                            coord1 = v2mm(int(tline[1]))
                            while True:
                                line = next(ddf).strip()
                                if len(line) > 1:
                                    tarr = line.split(' ')
                                    # print(tarr)
                                    coord2 = v2mm(float(tarr[0]))
                                    coord3 = v2mm(float(tarr[1]))
                                    netnr = int(tarr[2])
                                    tcode = int(tarr[3])
                                    ttype = int(tarr[4])
                                    orient = int(tarr[5][0])
                                    if(netnr == 65535):
                                        netnr = 0
                                    # print("Track ", layer, coord1, coord2, coord3, netnr, tcode, ttype, orient)
                                    # print(traceWidth)
                                    tstr = "  (segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width {width:.3f}) (layer {layer}) (net {netnr}))\n"
                                    match orient:
                                        case 1:
                                            tstr = tstr.format(x1 = coord2, y1 = -coord1, x2 = coord3, y2 = -coord1, netnr = netnr, layer = "\""+layers[layer]+"\"", width = v2mm(traceWidth[tcode]))
                                        case 2:
                                            tstr = tstr.format(x1 = coord1, y1 = -coord2, x2 = coord1, y2 = -coord3, netnr = netnr, layer = "\""+layers[layer]+"\"", width = v2mm(traceWidth[tcode]))
                                        case 4:
                                            tstr = tstr.format(x1 = coord2 + ((coord1 - coord2) / 2), y1 = -((coord1 - coord2) / -2), x2 = coord3 + ((coord1 - coord3) / 2 ), y2 = -((coord1 - coord3) / -2), netnr = netnr, layer = "\""+layers[layer]+"\"", width = v2mm(traceWidth[tcode]))
                                        case 8:
                                            tstr = tstr.format(x1 = coord2 - ((coord2 - coord1) / 2), y1 = -((coord2 - coord1) / -2), x2 = coord3 - ((coord3 - coord1) / 2 ), y2 = -((coord3 - coord1) / -2), netnr = netnr, layer = "\""+layers[layer]+"\"", width = v2mm(traceWidth[tcode]))
                                    
                                    # print(tstr)
                                    kicad.write(tstr)
                                if ';' in line:
                                    break

                        case 'V':
                            # print("Vector")
                            vline = [int(i) for i in line[4:].split(' ')]
                            # print(vline)
                            vlayer = int(vline[0])
                            vx1 = v2mm(int(vline[1]))
                            vy1 = -(v2mm(int(vline[2])))
                            vx2 = v2mm(int(vline[3]))
                            vy2 = -(v2mm(int(vline[4])))
                            vnetnr = int(vline[5])
                            if(vnetnr == 65535):
                                vnetnr = 0
                            vtcode = int(vline[6])
                            vttype = int(vline[7])
                            vstr = "  (segment (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) (width {width:.3f}) (layer {layer}) (net {netnr}))\n"
                            kicad.write(vstr.format(x1 = vx1, y1 = vy1, x2 = vx2, y2 = vy2, width = v2mm(traceWidth[vtcode]), layer = "\""+layers[vlayer]+"\"", netnr = vnetnr))
                        case 'A':
                            # print("Arc")
                            aline = [int(i) for i in line[4:].split(' ')]
                            # print(aline)
                            alayer = int(aline[0])
                            ax = v2mm(int(aline[1]))
                            ay = -(v2mm(int(aline[2])))
                            ar = v2mm(int(aline[3]))
                            arc1 = int(aline[4]) / 64
                            arc2 = int(aline[5]) / 64
                            anetnr = int(aline[6])
                            if(anetnr == 65535): anetnr = 0
                            atcode = int(aline[7])
                            if(atcode == 65535): atcode = 0
                            attype = int(aline[8])

                            arcStart = 360 + arc1
                            if(arcStart > 360): arcStart -= 360
                            arcEnd = arcStart + arc2
                            if(arcEnd > 360): arcEnd -= 360
                            xArcStart = ar * math.cos(math.pi / 180 * arcStart)
                            yArcStart = ar * math.sin(math.pi / 180 * arcStart)
                            xArcEnd   = ar * math.cos(math.pi / 180 * arcEnd)
                            yArcEnd   = ar * math.sin(math.pi / 180 * arcEnd)

                            astr = "  (gr_arc (start {xs:.4f} {ys:.4f}) (mid {xm:.4f} {ym:.4f}) (end {xe:.4f} {ye:.4f}) (width {width:.3f}) (layer {layer}))\n"
                            kicad.write(astr.format(xs = ax + xArcStart, ys = ay + yArcStart, xm = ax, ym = ay, xe = ax + xArcEnd, ye = ay + yArcEnd, width = v2mm(traceWidth[atcode]), layer = "\""+layers[alayer]+"\"", netnr = anetnr))
                        case 'P':
                            # print("Polygon")
                            lpline = [int(i) for i in line[4:].split(' ')]
                            # print(lpline)
                            lplayer = lpline[0]
                            lpnetnr = lpline[1]
                            if(lpnetnr == 65535): lpnetnr = 0
                            lppat   = lpline[2]
                            lpdist  = lpline[3]
                            lptcode = lpline[4]
                            lpclear = lpline[5]
                            lptype  = lpline[6]
                            lpstr = """  (zone (net {netnr})\n(net_name {netname}\")\n(layer \"{layer}\")\n
                                            (fill yes (thermal_gap 0.508) (thermal_bridge_width 0.508))\n
                                            (connect_pads (clearance 0.152))\n
                                            (polygon\n
                                                (pts\n
                                    """
                            kicad.write(lpstr.format(netnr = lpnetnr, netname = nets[lpnetnr], layer = layers[lplayer]))
                            while True:
                                line = next(ddf).strip()
                                if(line[0] == ';'): break
                                polyline = [v2mm(int(i)) for i in line.strip(':;').split(" ")]
                                for i,i2 in zip(polyline[::2],polyline[1::2]):
                                    kicad.write("(xy {x} {y})\n".format(x = i, y = -(i2)))
                                if ':' in line: break
                                if ';' in line: break

                            kicad.write("  )))\n")
                            # lpstr = """  (zone (net {netnr}) (net_name \"\") (layers \"F&B.Cu\" \"*.SilkS\" \"*.Mask\")\n
                            #                 (connect_pads yes (clearance 0))
                            #                 (keepout (tracks not_allowed) (vias not_allowed) (pads not_allowed) (copperpour not_allowed) (footprints allowed))
                            #                 (fill (thermal_gap 0.508) (thermal_bridge_width 0.508))\n
                            #                 (polygon\n
                            #                     (pts\n
                            #         """
                            # while True:
                            #     kicad.write(lpstr.format(netnr = lpnetnr))
                            #     while True:
                            #         line = next(ddf).strip()
                            #         if(line[0] == ';'): break
                            #         polyline = [v2mm(int(i)) for i in line.strip(':;').split(" ")]
                            #         for i,i2 in zip(polyline[::2],polyline[1::2]):
                            #             kicad.write("(xy {x} {y})\n".format(x = i, y = -(i2)))
                            #         if ':' in line: break
                            #         if ';' in line: break
                            #     kicad.write("  )))\n")
                            #     if ';' in line: break
                        case _:
                            print(line[2])
                case 'V':
                    # print("Vias")
                    varr = line[3:].split(" ")
                    # print(varr)
                    vxpos = v2mm(int(varr[0]))
                    while True:
                        line = next(ddf).strip()
                        if(line[0] == ';'):
                            break
                        vline = line.split(" ")
                        vypos = -(v2mm(int(vline[0])))
                        vnetnr = int(vline[1])
                        vpcode = int(vline[2])
                        vstr = "  (via (at {x} {y}) (size {s}) (drill {d:.2f}) (layers \"{lt}\" \"{lb}\") (net {n}))\n"
                        kicad.write(vstr.format(x = vxpos, y = vypos, s = v2mm(padT[vpcode]['Y']), d = drillCode[vpcode], lt = "F.Cu", lb = "B.Cu", n = vnetnr))
                        if ';' in line:
                            break

                case 'X':
                    # print("Text")
                    xtext = line[3:].split(" ", 7)
                    textx = v2mm(int(xtext[0]))
                    texty = -(v2mm(int(xtext[1])))
                    texth = v2mm(int(xtext[2]))
                    textw = v2mm(int(xtext[3]))
                    textt = v2mm(int(xtext[4])/5)
                    textr = int(xtext[5]) / 64
                    textl = int(xtext[6])
                    textstr = str_esc(xtext[7])
                    if textl == 2 or textl == 4:
                        textj = "(justify mirror)"
                    else:
                        textj = ''

                    # ['F.SilkS','F.Cu','B.Cu','In1.Cu','In2.Cu','F.Mask','B.Mask','B.SilkS','','Cmts.User','','','']
                    if textl == 0:
                        textl = 0 if textr > 0 else 7

                    thetext = "  (gr_text \"{tstr}\" (at {x} {y} {r}) (layer \"{tl}\") (effects (font (size {fh} {fw}) (thickness {thick})) {j}))\n"
                    kicad.write(thetext.format(tstr = textstr, x = textx, y = texty, r = textr, tl = layers[textl], fw = textw, fh = texth, thick = textt, j = textj))
                    # print(textstr)
                # case _:
                #     print(line[1])

        # kicad.write(line)
    # print(json.dumps(Shapes, indent=4))
    # print(nets)
    kicad.write(')')
    kicad.close()
    ddf.close()

