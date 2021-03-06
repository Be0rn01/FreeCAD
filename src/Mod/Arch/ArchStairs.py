#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2013                                                    *
#*   Yorik van Havre <yorik@uncreated.net>                                 *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

__title__="FreeCAD Arch Stairs"
__author__ = "Yorik van Havre"
__url__ = "http://www.freecadweb.org"

import FreeCAD,ArchComponent,ArchCommands,Draft,DraftVecUtils,math
from FreeCAD import Vector
if FreeCAD.GuiUp:
    import FreeCADGui
    from PySide import QtCore, QtGui
    from DraftTools import translate
    from PySide.QtCore import QT_TRANSLATE_NOOP
else:
    # \cond
    def translate(ctxt,txt):
        return txt
    def QT_TRANSLATE_NOOP(ctxt,txt):
        return txt
    # \endcond

## @package ArchStairs
#  \ingroup ARCH
#  \brief The Stairs object and tools
#
#  This module provides tools to build Stairs objects.


def makeStairs(baseobj=None,length=None,width=None,height=None,steps=None,name="Stairs"):

    """makeStairs([baseobj,length,width,height,steps]): creates a Stairs
    objects with given attributes."""

    if not FreeCAD.ActiveDocument:
        FreeCAD.Console.PrintError("No active document. Aborting\n")
        return
    p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Arch")
    obj = FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Stairs")
    obj.Label = translate("Arch",name)
    _Stairs(obj)
    if FreeCAD.GuiUp:
        _ViewProviderStairs(obj.ViewObject)
    if baseobj:
        obj.Base = baseobj
    if length:
        obj.Length = length
    else:
        obj.Length = p.GetFloat("StairsLength",4500.0)
    if width:
        obj.Width = width
    else:
        obj.Width = p.GetFloat("StairsWidth",1000.0)
    if height:
        obj.Height = height
    else:
        obj.Height = p.GetFloat("StairsHeight",3000.0)
    if steps:
        obj.NumberOfSteps = steps

    obj.Structure = "Massive"
    obj.StructureThickness = 150

    return obj


class _CommandStairs:

    "the Arch Stairs command definition"

    def GetResources(self):

        return {'Pixmap'  : 'Arch_Stairs',
                'MenuText': QT_TRANSLATE_NOOP("Arch_Stairs","Stairs"),
                'Accel': "S, R",
                'ToolTip': QT_TRANSLATE_NOOP("Arch_Space","Creates a stairs object")}

    def IsActive(self):

        return not FreeCAD.ActiveDocument is None

    def Activated(self):

        p = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Arch")
        FreeCAD.ActiveDocument.openTransaction(translate("Arch","Create Stairs"))
        FreeCADGui.addModule("Arch")

        # a list of 'segment' / 'flight' of stairs
        stairs = []
        additions = []
        lenSelection = len(FreeCADGui.Selection.getSelection())

        if lenSelection > 0:
            if lenSelection > 1:
                stairs.append(makeStairs(None, None, None, None, None))
                i = 1
            else:
                i = 0

            for obj in FreeCADGui.Selection.getSelection():
                print (obj.Name)
                if (len(obj.Shape.Edges) > 1):
                    stairs.append(makeStairs(obj, None, None, None, 1))
                else:
                    stairs.append(makeStairs(obj, None, None, None, 16))
                if i > 1:
                    additions.append(stairs[i])
                    stairs[i].LastSegment = stairs[i-1]
                else:
                    if len(stairs) > 1:						# i.e. length >1, have a 'master' staircase created
                        stairs[0].Base = stairs[i]
                i += 1
            print(stairs)
            if lenSelection > 1:
                stairs[0].Additions = additions

        else:
            FreeCADGui.doCommand("obj = Arch.makeStairs(steps="+str(p.GetInt("StairsSteps",17))+")")
        FreeCADGui.addModule("Draft")

        for obj in stairs:
                Draft.autogroup(obj) # seems not working?

        FreeCAD.ActiveDocument.commitTransaction()
        FreeCAD.ActiveDocument.recompute()


class _Stairs(ArchComponent.Component):

    "A stairs object"

    def __init__(self,obj):

        ArchComponent.Component.__init__(self,obj)
        self.setProperties(obj)
        obj.IfcRole = "Stair"

    def setProperties(self,obj):

        # http://en.wikipedia.org/wiki/Stairs

        pl = obj.PropertiesList

        # base properties
        if not "Length" in pl:
            obj.addProperty("App::PropertyLength","Length","Stairs",QT_TRANSLATE_NOOP("App::Property","The length of these stairs, if no baseline is defined"))
        if not "Width" in pl:
            obj.addProperty("App::PropertyLength","Width","Stairs",QT_TRANSLATE_NOOP("App::Property","The width of these stairs"))
        if not "Height" in pl:
            obj.addProperty("App::PropertyLength","Height","Stairs",QT_TRANSLATE_NOOP("App::Property","The total height of these stairs"))
        if not "Align" in pl:
            obj.addProperty("App::PropertyEnumeration","Align","Stairs",QT_TRANSLATE_NOOP("App::Property","The alignment of these stairs on their baseline, if applicable"))
            obj.Align = ['Left','Right','Center']

        # steps properties
        if not "NumberOfSteps" in pl:
            obj.addProperty("App::PropertyInteger","NumberOfSteps","Steps",QT_TRANSLATE_NOOP("App::Property","The number of risers in these stairs"))
        if not "TreadDepth" in pl:
            obj.addProperty("App::PropertyLength","TreadDepth","Steps",QT_TRANSLATE_NOOP("App::Property","The depth of the treads of these stairs"))
            obj.setEditorMode("TreadDepth",1)
        if not "RiserHeight" in pl:
            obj.addProperty("App::PropertyLength","RiserHeight","Steps",QT_TRANSLATE_NOOP("App::Property","The height of the risers of these stairs"))
            obj.setEditorMode("RiserHeight",1)
        if not "Nosing" in pl:
            obj.addProperty("App::PropertyLength","Nosing","Steps",QT_TRANSLATE_NOOP("App::Property","The size of the nosing"))
        if not "TreadThickness" in pl:
            obj.addProperty("App::PropertyLength","TreadThickness","Steps",QT_TRANSLATE_NOOP("App::Property","The thickness of the treads"))
        if not "BlondelRatio" in pl:
            obj.addProperty("App::PropertyFloat","BlondelRatio","Steps",QT_TRANSLATE_NOOP("App::Property","The Blondel ratio indicates comfortable stairs and should be between 62 and 64cm or 24.5 and 25.5in"))
            obj.setEditorMode("BlondelRatio",1)
        if not hasattr(obj,"LandingDepth"):
            obj.addProperty("App::PropertyLength","LandingDepth","Steps",QT_TRANSLATE_NOOP("App::Property","The depth of the landing of these stairs"))
        if not hasattr(obj,"Flight"):
            obj.addProperty("App::PropertyEnumeration","Flight","Structure",QT_TRANSLATE_NOOP("App::Property","The direction of of flight after landing"))
            obj.Flight = ["Straight","HalfTurnLeft","HalfTurnRight"]

        # Segment properties
        if not hasattr(obj,"LastSegment"):
            obj.addProperty("App::PropertyLink","LastSegment","Segment","Last Segment (Flight or Landing) of Arch Stairs connecting to This Segment")
        if not hasattr(obj,"AbsTop"):
            obj.addProperty("App::PropertyVector","AbsTop","Segment",QT_TRANSLATE_NOOP("App::Property","The 'absolute' top level of a flight of stairs leads to "))
            obj.setEditorMode("AbsTop",1)

        # structural properties
        if not "Landings" in pl:
            obj.addProperty("App::PropertyEnumeration","Landings","Structure",QT_TRANSLATE_NOOP("App::Property","The type of landings of these stairs"))
            obj.Landings = ["None","At center","At each corner"]
        if not "Winders" in pl:
            obj.addProperty("App::PropertyEnumeration","Winders","Structure",QT_TRANSLATE_NOOP("App::Property","The type of winders in these stairs"))
            obj.Winders = ["None","All","Corners strict","Corners relaxed"]
        if not "Structure" in pl:
            obj.addProperty("App::PropertyEnumeration","Structure","Structure",QT_TRANSLATE_NOOP("App::Property","The type of structure of these stairs"))
            obj.Structure = ["None","Massive","One stringer","Two stringers"]
        if not "StructureThickness" in pl:
            obj.addProperty("App::PropertyLength","StructureThickness","Structure",QT_TRANSLATE_NOOP("App::Property","The thickness of the massive structure or of the stringers"))
        if not "StringerWidth" in pl:
            obj.addProperty("App::PropertyLength","StringerWidth","Structure",QT_TRANSLATE_NOOP("App::Property","The width of the stringers"))
        if not "StructureOffset" in pl:
            obj.addProperty("App::PropertyLength","StructureOffset","Structure",QT_TRANSLATE_NOOP("App::Property","The offset between the border of the stairs and the structure"))
        if not "StringerOverlap" in pl:
            obj.addProperty("App::PropertyLength","StringerOverlap","Structure",QT_TRANSLATE_NOOP("App::Property","The overlap of the stringers above the bottom of the treads"))

        self.Type = "Stairs"

    def onDocumentRestored(self,obj):

        ArchComponent.Component.onDocumentRestored(self,obj)
        self.setProperties(obj)

    def execute(self,obj):

        "constructs the shape of the stairs"

        if self.clone(obj):
            return

        import Part
        self.steps = []
        self.pseudosteps = []
        self.structures = []
        pl = obj.Placement
        landings = 0

        base = None

        if obj.Base:
            if hasattr(obj.Base,"Shape"):
                if obj.Base.Shape:
                    if obj.Base.Shape.Solids:
                        base = obj.Base.Shape.copy()

        # special case NumberOfSteps = 1 : multi-edges landing
        if (not base) and obj.Width.Value and obj.Height.Value and (obj.NumberOfSteps > 0):
            if obj.Base:
                if not obj.Base.isDerivedFrom("Part::Feature"):
                    return
                if obj.Base.Shape.Solids:
                    obj.Shape = obj.Base.Shape.copy()
                    obj.Placement = FreeCAD.Placement(obj.Base.Placement).multiply(pl)
                    obj.TreadDepth = 0.0
                    obj.RiserHeight = 0.0
                    return
                if not obj.Base.Shape.Edges:
                    return
                if obj.Base.Shape.Faces:
                    return
                if (len(obj.Base.Shape.Edges) == 1):
                    edge = obj.Base.Shape.Edges[0]
                    if isinstance(edge.Curve,(Part.LineSegment,Part.Line)):
                      # preparing for multi-edges landing / segment staircase
                      if obj.NumberOfSteps > 1:

                        if obj.Landings == "At center":
                            landings = 1
                            self.makeStraightStairsWithLanding(obj,edge)
                        else:
                            self.makeStraightStairs(obj,edge)

                      # preparing for multi-edges landing / segment staircase
                      if obj.NumberOfSteps == 1:
                            # TODO - All use self.makeMultiEdgesLanding(obj,edges) ?
                            self.makeStraightLanding(obj,edge)
                      if obj.NumberOfSteps == 0:
                            pass # Should delete the whole shape

                    else:
                        if obj.Landings == "At center":
                            landings = 1
                            self.makeCurvedStairsWithLandings(obj,edge)
                        else:
                            self.makeCurvedStairs(obj,edge)

                elif (len(obj.Base.Shape.Edges) >= 1):
                      if obj.NumberOfSteps == 1:
                            edges = obj.Base.Shape.Edges
                            self.makeMultiEdgesLanding(obj,edges)

            else:
                if not obj.Length.Value:
                    return
                edge = Part.LineSegment(Vector(0,0,0),Vector(obj.Length.Value,0,0)).toShape()
                if obj.Landings == "At center":
                    landings = 1
                    self.makeStraightStairsWithLanding(obj,edge)
                else:
                    self.makeStraightStairs(obj,edge)

        if self.structures or self.steps:
            base = Part.makeCompound(self.structures + self.steps)
        elif self.pseudosteps:
            shape = Part.makeCompound(self.pseudosteps)
            obj.Shape = shape
            obj.Placement = pl
            return

        base = self.processSubShapes(obj,base,pl)
        if base:
            if not base.isNull():
                obj.Shape = base
                obj.Placement = pl

        # compute step data
        if obj.NumberOfSteps > 1:
            l = obj.Length.Value
            h = obj.Height.Value
            if obj.Base:
                if obj.Base.isDerivedFrom("Part::Feature"):
                    l = obj.Base.Shape.Length
                    if obj.Base.Shape.BoundBox.ZLength:
                        h = obj.Base.Shape.BoundBox.ZLength
            if obj.LandingDepth:
                obj.TreadDepth = float(l-(landings*obj.LandingDepth.Value))/(obj.NumberOfSteps-(1+landings))
            else:
                obj.TreadDepth = float(l-(landings*obj.Width.Value))/(obj.NumberOfSteps-(1+landings))
            obj.RiserHeight = float(h)/obj.NumberOfSteps
            obj.BlondelRatio = obj.RiserHeight.Value*2+obj.TreadDepth.Value

    def align(self,basepoint,align,widthvec):

        "moves a given basepoint according to the alignment"
        if align == "Center":
            basepoint = basepoint.add(DraftVecUtils.scale(widthvec,-0.5))
        elif align == "Right":
            basepoint = basepoint.add(DraftVecUtils.scale(widthvec,-1))
        return basepoint


    def makeMultiEdgesLanding(self,obj,edges):

        "builds a 'multi-edges' landing from edges" # 'copying' from makeStraightLanding()

        import Part,DraftGeomUtils

        v, vLength, vWidth, vBase = [], [], [], []
        p1o, p2o, p1, p2, p3, p4 = [], [], [], [], [], []
        outline, outlineP1P2, outlineP3P4 = [], [], []

        enum_edges = enumerate(edges)
        for i, edge in enum_edges:
            v.append(DraftGeomUtils.vec(edge))
            vLength.append(Vector(v[i].x,v[i].y,0))
            # TODO obj.Width[i].Value for different 'edges' / 'sections' of the landing
            vWidth.append(DraftVecUtils.scaleTo(vLength[i].cross(Vector(0,0,1)),obj.Width.Value))
            vBase.append(edges[i].Vertexes[0].Point)
            vBase[i] = self.vbaseFollowLastSement(obj, vBase[i])

            # step + structure							# assume all left-align first # no nosing
            p1o.append(vBase[i].add(Vector(0,0,-abs(obj.TreadThickness.Value))))
            p2o.append(p1o[i].add(vLength[i]))
            p1.append(self.align(vBase[i],obj.Align,vWidth[i]).add(Vector(0,0,-abs(obj.TreadThickness.Value))))
            p2.append(p1[i].add(vLength[i]))
            p3.append(p2[i].add(vWidth[i]))
            p4.append(p3[i].add(DraftVecUtils.neg(vLength[i])))


            if obj.Align == 'Left':
                outlineP1P2.append(p1[i])
                outlineP1P2.append(p2[i])					# can better skip 1 'supposedly' overlapping point every pair?
                if i > 0:
                    print ("Debug - intersection calculation")
                    print (p3[i-1])
                    print (p4[i-1])
                    print (p3[i])
                    print (p4[i])
                    intersection = DraftGeomUtils.findIntersection(p3[i-1],p4[i-1],p3[i],p4[i],True,True)
                    print (intersection)
                    outlineP3P4.insert(0, intersection[0])
                else:
                    outlineP3P4.insert(0, p4[i])

            elif obj.Align == 'Right':
                if i > 0:
                    intersection = DraftGeomUtils.findIntersection(p1[i-1],p2[i-1],p1[i],p2[i],True,True)
                    outlineP1P2.append(intersection[0])
                else:
                    outlineP1P2.append(p1[i])
                outlineP3P4.insert(0, p4[i])
                outlineP3P4.insert(0, p3[i])

            elif obj.Align == 'Center':
                if i > 0:
                    intersection = DraftGeomUtils.findIntersection(p1[i-1],p2[i-1],p1[i],p2[i],True,True)
                    outlineP1P2.append(intersection[0])
                    intersection = DraftGeomUtils.findIntersection(p3[i-1],p4[i-1],p3[i],p4[i],True,True)
                    outlineP3P4.insert(0, intersection[0])
                else:
                    outlineP1P2.append(p1[i])
                    outlineP3P4.insert(0, p4[i])

            else:
                outlineP1P2.append(p1[i])
                outlineP1P2.append(p2[i])
                outlineP3P4.insert(0, p4[i])
                outlineP3P4.insert(0, p3[i])

        # add back last/first 'missing' point(s)
        if obj.Align in ['Left', 'Center']:
            outlineP3P4.insert(0, p3[i])
        if obj.Align in ['Right', 'Center']:
            outlineP1P2.append(p2[i])

        outline = outlineP1P2 + outlineP3P4
        outline.append(p1[0])
        print (outlineP1P2)
        print (outlineP3P4)
        print (outline)

        stepFace = Part.Face(Part.makePolygon(outline))

        if obj.TreadThickness.Value:
            step = stepFace.extrude(Vector(0,0,abs(obj.TreadThickness.Value)))
            self.steps.append(step)
        else:
            self.pseudosteps.append(stepFace)

        if obj.StructureThickness.Value:
            landingFace = stepFace
            struct = landingFace.extrude(Vector(0,0,-abs(obj.StructureThickness.Value)))

        if struct:
            self.structures.append(struct)

        obj.AbsTop = vBase[1]

    @staticmethod
    def vbaseFollowLastSement(obj, vBase):
        if obj.LastSegment:
            lastSegmentAbsTop = obj.LastSegment.AbsTop
            vBase = Vector(vBase.x, vBase.y,lastSegmentAbsTop.z) # use Last Segment top's z-coordinate 
        return vBase


    # Add flag (temporarily?) for indicating which method call this to determine whether the landing has been 're-based' before or not
    def makeStraightLanding(self,obj,edge,numberofsteps=None, callByMakeStraightStairsWithLanding=False):	# what is use of numberofsteps ?
        "builds a landing from a straight edge"

        # general data
        if not numberofsteps:
            numberofsteps = obj.NumberOfSteps
        import Part,DraftGeomUtils
        v = DraftGeomUtils.vec(edge)
        vLength = Vector(v.x,v.y,0)
        vWidth = vWidth = DraftVecUtils.scaleTo(vLength.cross(Vector(0,0,1)),obj.Width.Value)
        vBase = edge.Vertexes[0].Point

        # if not call by makeStraightStairsWithLanding() - not 're-base' in function there, then 're-base' here
        if not callByMakeStraightStairsWithLanding:
            vBase = self.vbaseFollowLastSement(obj, vBase)
            obj.AbsTop = vBase

        vNose = DraftVecUtils.scaleTo(vLength,-abs(obj.Nosing.Value))
        h = obj.Height.Value
        l = obj.Length.Value
        if obj.Base:
            if obj.Base.isDerivedFrom("Part::Feature"):
                l = obj.Base.Shape.Length
                if obj.Base.Shape.BoundBox.ZLength:
                    h = obj.Base.Shape.BoundBox.ZLength

        if obj.LandingDepth:
            fLength = float(l-obj.LandingDepth.Value)/(numberofsteps-2)
        else:
            fLength = float(l-obj.Width.Value)/(numberofsteps-2)

        fHeight = float(h)/numberofsteps
        a = math.atan(fHeight/fLength)
        print("landing data:",fLength,":",fHeight)

        # step
        p1 = self.align(vBase,obj.Align,vWidth)
        p1o = p1.add(Vector(0,0,-abs(obj.TreadThickness.Value)))

        p1 = p1.add(vNose).add(Vector(0,0,-abs(obj.TreadThickness.Value)))
        p2 = p1.add(DraftVecUtils.neg(vNose)).add(vLength)
        p3 = p2.add(vWidth)
        p4 = p3.add(DraftVecUtils.neg(vLength)).add(vNose)

        p4o = p3.add(DraftVecUtils.neg(vLength))
        if not callByMakeStraightStairsWithLanding:
            p2o = p2
            p3o = p3

        if obj.Flight == "HalfTurnLeft":
            p1 = p1.add(-vWidth)
            p2 = p2.add(-vWidth)
        elif obj.Flight == "HalfTurnRight":
            p3 = p3.add(vWidth)
            p4 = p4.add(vWidth)

        step = Part.Face(Part.makePolygon([p1,p2,p3,p4,p1]))
        if obj.TreadThickness.Value:
            step = step.extrude(Vector(0,0,abs(obj.TreadThickness.Value)))
            self.steps.append(step)
        else:
            self.pseudosteps.append(step)

        # structure
        lProfile = []
        struct = None
        p7 = None
        p1 = p1.add(DraftVecUtils.neg(vNose))
        p2 = p1.add(Vector(0,0,-fHeight)).add(Vector(0,0,-obj.StructureThickness.Value/math.cos(a)))
        resheight = p1.sub(p2).Length - obj.StructureThickness.Value
        reslength = resheight / math.tan(a)
        p3 = p2.add(DraftVecUtils.scaleTo(vLength,reslength)).add(Vector(0,0,resheight))
        p6 = p1.add(vLength)
        if obj.TreadThickness.Value:
            if obj.Flight == "Straight":
                p7 = p6.add(Vector(0,0,obj.TreadThickness.Value))
        reslength = fLength + (obj.StructureThickness.Value/math.sin(a)-(fHeight-obj.TreadThickness.Value)/math.tan(a))
        if p7:
            p5 = p7.add(DraftVecUtils.scaleTo(vLength,reslength))
        else:
            if obj.Flight == "Straight":
                p5 = p6.add(DraftVecUtils.scaleTo(vLength,reslength))
            else:
                p5 = None
        resheight = obj.StructureThickness.Value + obj.TreadThickness.Value
        reslength = resheight/math.tan(a)
        if obj.Flight == "Straight":
            p4 = p5.add(DraftVecUtils.scaleTo(vLength,-reslength)).add(Vector(0,0,-resheight))
        else:
            p4 = p6.add(Vector(0,0,-obj.StructureThickness.Value))
        if obj.Structure == "Massive":
            if obj.StructureThickness.Value:
                if p7:
                    struct = Part.Face(Part.makePolygon([p1,p2,p3,p4,p5,p7,p6,p1]))
                elif p5:
                    struct = Part.Face(Part.makePolygon([p1,p2,p3,p4,p5,p6,p1]))
                else:
                    struct = Part.Face(Part.makePolygon([p1,p2,p3,p4,p6,p1]))
                evec = vWidth
                mvec = FreeCAD.Vector(0.0,0)
                if obj.StructureOffset.Value:
                    mvec = DraftVecUtils.scaleTo(vWidth,obj.StructureOffset.Value)
                    struct.translate(mvec)
                if obj.Flight in ["HalfTurnLeft","HalfTurnRight"]:
                    evec = DraftVecUtils.scaleTo(evec,2*evec.Length-2*mvec.Length)
                else:
                    evec = DraftVecUtils.scaleTo(evec,evec.Length-(2*mvec.Length))
                struct = struct.extrude(evec)
        elif obj.Structure in ["One stringer","Two stringers"]:
            if obj.StringerWidth.Value and obj.StructureThickness.Value:
                p1b = p1.add(Vector(0,0,-fHeight))
                reslength = fHeight/math.tan(a)
                p1c = p1.add(DraftVecUtils.scaleTo(vLength,reslength))
                p5b = None
                p5c = None
                if obj.TreadThickness.Value:
                    reslength = obj.StructureThickness.Value/math.sin(a)
                    p5b = p5.add(DraftVecUtils.scaleTo(vLength,-reslength))
                    reslength = obj.TreadThickness.Value/math.tan(a)
                    p5c = p5b.add(DraftVecUtils.scaleTo(vLength,-reslength)).add(Vector(0,0,-obj.TreadThickness.Value))
                    pol = Part.Face(Part.makePolygon([p1c,p1b,p2,p3,p4,p5,p5b,p5c,p1c]))
                else:
                    pol = Part.Face(Part.makePolygon([p1c,p1b,p2,p3,p4,p5,p1c]))
                evec = DraftVecUtils.scaleTo(vWidth,obj.StringerWidth.Value)
                if obj.Structure == "One stringer":
                    if obj.StructureOffset.Value:
                        mvec = DraftVecUtils.scaleTo(vWidth,obj.StructureOffset.Value)
                    else:
                        mvec = DraftVecUtils.scaleTo(vWidth,(vWidth.Length/2)-obj.StringerWidth.Value/2)
                    pol.translate(mvec)
                    struct = pol.extrude(evec)
                elif obj.Structure == "Two stringers":
                    pol2 = pol.copy()
                    if obj.StructureOffset.Value:
                        mvec = DraftVecUtils.scaleTo(vWidth,obj.StructureOffset.Value)
                        pol.translate(mvec)
                        mvec = vWidth.add(mvec.negative())
                        pol2.translate(mvec)
                    else:
                        pol2.translate(vWidth)
                    s1 = pol.extrude(evec)
                    s2 = pol2.extrude(evec.negative())
                    struct = Part.makeCompound([s1,s2])

        # Overwriting result of above functions if case fit - should better avoid running the above in first place (better rewrite later)
        if not callByMakeStraightStairsWithLanding:
            if obj.StructureThickness.Value:
                struct = None
                landingFace = Part.Face(Part.makePolygon([p1o,p2o,p3o,p4o,p1o]))
                struct = landingFace.extrude(Vector(0,0,-abs(obj.StructureThickness.Value)))

        if struct:
            self.structures.append(struct)


    def makeStraightStairs(self,obj,edge,numberofsteps=None):

        "builds a simple, straight staircase from a straight edge"

        # Upgrade obj if it is from an older version of FreeCAD
        if not(hasattr(obj, "StringerOverlap")):
            obj.addProperty("App::PropertyLength","StringerOverlap","Structure",QT_TRANSLATE_NOOP("App::Property","The overlap of the stringers above the bottom of the treads"))

        # general data
        import Part,DraftGeomUtils
        if not numberofsteps:
            numberofsteps = obj.NumberOfSteps
            # if not numberofsteps - not call by makeStraightStairsWithLanding()
            # if not 're-base' there (StraightStair is part of StraightStairsWithLanding 'flight'), then 're-base' here (StraightStair is individual 'flight')
            callByMakeStraightStairsWithLanding = False
        else:
            callByMakeStraightStairsWithLanding = True

        v = DraftGeomUtils.vec(edge)
        vLength = DraftVecUtils.scaleTo(v,float(edge.Length)/(numberofsteps-1))
        vLength = Vector(vLength.x,vLength.y,0)
        if round(v.z,Draft.precision()) != 0:
            h = v.z
        else:
            h = obj.Height.Value
        vHeight = Vector(0,0,float(h)/numberofsteps)
        vWidth = DraftVecUtils.scaleTo(vLength.cross(Vector(0,0,1)),obj.Width.Value)
        vBase = edge.Vertexes[0].Point

        if not callByMakeStraightStairsWithLanding:
            if obj.LastSegment:
                print("obj.LastSegment is: " )
                print(obj.LastSegment.Name)
                lastSegmentAbsTop = obj.LastSegment.AbsTop
                print("lastSegmentAbsTop is: ")
                print(lastSegmentAbsTop)
                vBase = Vector(vBase.x, vBase.y,lastSegmentAbsTop.z)		# use Last Segment top's z-coordinate 
            obj.AbsTop = vBase.add(Vector(0,0,h))

        vNose = DraftVecUtils.scaleTo(vLength,-abs(obj.Nosing.Value))
        a = math.atan(vHeight.Length/vLength.Length)

        # steps
        for i in range(numberofsteps-1):
            p1 = vBase.add((Vector(vLength).multiply(i)).add(Vector(vHeight).multiply(i+1)))
            p1 = self.align(p1,obj.Align,vWidth)
            p1 = p1.add(vNose).add(Vector(0,0,-abs(obj.TreadThickness.Value)))
            p2 = p1.add(DraftVecUtils.neg(vNose)).add(vLength)
            p3 = p2.add(vWidth)
            p4 = p3.add(DraftVecUtils.neg(vLength)).add(vNose)
            step = Part.Face(Part.makePolygon([p1,p2,p3,p4,p1]))
            if obj.TreadThickness.Value:
                step = step.extrude(Vector(0,0,abs(obj.TreadThickness.Value)))
                self.steps.append(step)
            else:
                self.pseudosteps.append(step)

        # structure
        lProfile = []
        struct = None
        if obj.Structure == "Massive":
            if obj.StructureThickness.Value:

                # Massive Structure to respect 'align' attribute
                vBasedAligned = self.align(vBase,obj.Align,vWidth)
                vBase = vBasedAligned

                for i in range(numberofsteps-1):
                    if not lProfile:
                        lProfile.append(vBase)
                    last = lProfile[-1]
                    if len(lProfile) == 1:
                        last = last.add(Vector(0,0,-abs(obj.TreadThickness.Value)))
                    lProfile.append(last.add(vHeight))
                    lProfile.append(lProfile[-1].add(vLength))
                resHeight1 = obj.StructureThickness.Value/math.cos(a)
                lProfile.append(lProfile[-1].add(Vector(0,0,-resHeight1)))
                resHeight2 = ((numberofsteps-1)*vHeight.Length)-(resHeight1+obj.TreadThickness.Value)
                resLength = (vLength.Length/vHeight.Length)*resHeight2
                h = DraftVecUtils.scaleTo(vLength,-resLength)
                lProfile.append(lProfile[-1].add(Vector(h.x,h.y,-resHeight2)))
                lProfile.append(vBase)
                #print(lProfile)
                pol = Part.makePolygon(lProfile)
                struct = Part.Face(pol)
                evec = vWidth
                if obj.StructureOffset.Value:
                    mvec = DraftVecUtils.scaleTo(vWidth,obj.StructureOffset.Value)
                    struct.translate(mvec)
                    evec = DraftVecUtils.scaleTo(evec,evec.Length-(2*mvec.Length))
                struct = struct.extrude(evec)
        elif obj.Structure in ["One stringer","Two stringers"]:
            if obj.StringerWidth.Value and obj.StructureThickness.Value:
                hyp = math.sqrt(vHeight.Length**2 + vLength.Length**2)
                l1 = Vector(vLength).multiply(numberofsteps-1)
                h1 = Vector(vHeight).multiply(numberofsteps-1).add(Vector(0,0,-abs(obj.TreadThickness.Value)+obj.StringerOverlap.Value))
                p1 = vBase.add(l1).add(h1)
                p1 = self.align(p1,obj.Align,vWidth)
                if obj.StringerOverlap.Value <= float(h)/numberofsteps:
                    lProfile.append(p1)
                else:
                    p1b = vBase.add(l1).add(Vector(0,0,float(h)))
                    p1a = p1b.add(Vector(vLength).multiply((p1b.z-p1.z)/vHeight.Length))
                    lProfile.append(p1a)
                    lProfile.append(p1b)
                h2 = (obj.StructureThickness.Value/vLength.Length)*hyp
                lProfile.append(p1.add(Vector(0,0,-abs(h2))))
                h3 = lProfile[-1].z-vBase.z
                l3 = (h3/vHeight.Length)*vLength.Length
                v3 = DraftVecUtils.scaleTo(vLength,-l3)
                lProfile.append(lProfile[-1].add(Vector(0,0,-abs(h3))).add(v3))
                l4 = (obj.StructureThickness.Value/vHeight.Length)*hyp
                v4 = DraftVecUtils.scaleTo(vLength,-l4)
                lProfile.append(lProfile[-1].add(v4))
                lProfile.append(lProfile[0])
                #print(lProfile)
                pol = Part.makePolygon(lProfile)
                pol = Part.Face(pol)
                evec = DraftVecUtils.scaleTo(vWidth,obj.StringerWidth.Value)
                if obj.Structure == "One stringer":
                    if obj.StructureOffset.Value:
                        mvec = DraftVecUtils.scaleTo(vWidth,obj.StructureOffset.Value)
                    else:
                        mvec = DraftVecUtils.scaleTo(vWidth,(vWidth.Length/2)-obj.StringerWidth.Value/2)
                    pol.translate(mvec)
                    struct = pol.extrude(evec)
                elif obj.Structure == "Two stringers":
                    pol2 = pol.copy()
                    if obj.StructureOffset.Value:
                        mvec = DraftVecUtils.scaleTo(vWidth,obj.StructureOffset.Value)
                        pol.translate(mvec)
                        mvec = vWidth.add(mvec.negative())
                        pol2.translate(mvec)
                    else:
                        pol2.translate(vWidth)
                    s1 = pol.extrude(evec)
                    s2 = pol2.extrude(evec.negative())
                    struct = Part.makeCompound([s1,s2])
        if struct:
            self.structures.append(struct)


    def makeStraightStairsWithLanding(self,obj,edge):

        "builds a straight staircase with a landing in the middle"

        if obj.NumberOfSteps < 3:
            return
        import Part,DraftGeomUtils
        v = DraftGeomUtils.vec(edge)
        if obj.LandingDepth:
            reslength = edge.Length - obj.LandingDepth.Value
        else:
            reslength = edge.Length - obj.Width.Value
        vLength = DraftVecUtils.scaleTo(v,float(reslength)/(obj.NumberOfSteps-2))
        vLength = Vector(vLength.x,vLength.y,0)
        vWidth = DraftVecUtils.scaleTo(vLength.cross(Vector(0,0,1)),obj.Width.Value)
        p1 = edge.Vertexes[0].Point
        if round(v.z,Draft.precision()) != 0:
            h = v.z
        else:
            h = obj.Height.Value
        hstep = h/obj.NumberOfSteps
        landing = int(obj.NumberOfSteps/2)
        if obj.LastSegment:
                print("obj.LastSegment is: " )
                print(obj.LastSegment.Name)
                lastSegmentAbsTop = obj.LastSegment.AbsTop
                print("lastSegmentAbsTop is: ")
                print(lastSegmentAbsTop)
                p1 = Vector(p1.x, p1.y,lastSegmentAbsTop.z)			# use Last Segment top's z-coordinate 
                print(p1)
        obj.AbsTop = p1.add(Vector(0,0,h))
        p2 = p1.add(DraftVecUtils.scale(vLength,landing-1).add(Vector(0,0,landing*hstep)))
        if obj.LandingDepth:
            p3 = p2.add(DraftVecUtils.scaleTo(vLength,obj.LandingDepth.Value))
        else:
            p3 = p2.add(DraftVecUtils.scaleTo(vLength,obj.Width.Value))
        if obj.Flight in ["HalfTurnLeft", "HalfTurnRight"]:
            if (obj.Align == "Left" and obj.Flight == "HalfTurnLeft") or (obj.Align == "Right" and obj.Flight == "HalfTurnRight"):
                p3r = p2
            elif (obj.Align == "Left" and obj.Flight == "HalfTurnRight"):
                p3r = self.align(p2,"Right",-2*vWidth) # -ve / opposite direction of "Right" - no "Left" in _Stairs.Align()
            elif (obj.Align == "Right" and obj.Flight == "HalfTurnLeft"):
                p3r = self.align(p2,"Right",2*vWidth)
            elif (obj.Align == "Center" and obj.Flight == "HalfTurnLeft"):
                p3r = self.align(p2,"Right",vWidth)
            elif (obj.Align == "Center" and obj.Flight == "HalfTurnRight"):
                p3r = self.align(p2,"Right",-vWidth) # -ve / opposite direction of "Right" - no "Left" in _Stairs.Align()
            else:
                print("Should have a bug here, if see this")
            p4r = p3r.add(DraftVecUtils.scale(-vLength,obj.NumberOfSteps-(landing+1)).add(Vector(0,0,(obj.NumberOfSteps-landing)*hstep)))
        else:
            p4 = p3.add(DraftVecUtils.scale(vLength,obj.NumberOfSteps-(landing+1)).add(Vector(0,0,(obj.NumberOfSteps-landing)*hstep)))
        self.makeStraightStairs(obj,Part.LineSegment(p1,p2).toShape(),landing)
        self.makeStraightLanding(obj,Part.LineSegment(p2,p3).toShape(), None, True)
        if obj.Flight in ["HalfTurnLeft", "HalfTurnRight"]:
            self.makeStraightStairs(obj,Part.LineSegment(p3r,p4r).toShape(),obj.NumberOfSteps-landing)
        else:
            self.makeStraightStairs(obj,Part.LineSegment(p3,p4).toShape(),obj.NumberOfSteps-landing)


    def makeCurvedStairs(self,obj,edge):

        print("Not yet implemented!")

    def makeCurvedStairsWithLanding(self,obj,edge):

        print("Not yet implemented!")


class _ViewProviderStairs(ArchComponent.ViewProviderComponent):

    "A View Provider for Stairs"

    def __init__(self,vobj):

        ArchComponent.ViewProviderComponent.__init__(self,vobj)

    def getIcon(self):

        import Arch_rc
        return ":/icons/Arch_Stairs_Tree.svg"


if FreeCAD.GuiUp:
    FreeCADGui.addCommand('Arch_Stairs',_CommandStairs())
