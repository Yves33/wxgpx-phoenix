from wxmappanel.wxmappanel import WxMapLayer

class WxOverlayLayer(WxMapLayer):
        def __init__(self,parent,name="Overlay"):
            WxMapLayer.__init__(self,parent,name)
            self.instructions=[]
            self.screenunits=True

        def ToScreen(self,x,y=None):
            if not self.screenunits:
                if y!=None:
                    return self.parent.GeoToScreen(x,y)
                else:
                    return x/self.parent.pixelscale
            else:
                if y!=None:
                    return (x,y)
                else:
                    return x

        def Clear(self):
            self.instructions[:]=[]
            self.parent.Clear()

        def DrawOffscreen(self,dc):
            width,height=self.parent.GetClientSize()
            pen=self.parent.renderer
            for instr in self.instructions:
                if instr[0]=='pen':
                    pen.SetLineWidth(instr[1])
                if instr[0]=='pencolor':
                    pen.SetPenColor(instr[1],instr[2],instr[3],instr[4])
                if instr[0]=='brushcolor':
                    pen.SetBrushColor(instr[1],instr[2],instr[3],instr[4])
                if instr[0]=='screen':   # we are specifying screen coordinates. don't need to convert
                    self.screenunits=True
                if instr[0]=='geo':      # we are specifying geographic coordinates. always convert
                    self.screenunits=False
                if instr[0]=='circle':   # Line, Lines, Text, Rect, Circle, Polygon
                    x1,y1=x1,y1=self.ToScreen(instr[1],instr[2])
                    r=self.ToScreen(instr[3])
                    pen.Circle(x1,y1,r)
                if instr[0]=='rect':
                    x1,y1=self.ToScreen(instr[1],instr[2])
                    x2,y2=self.ToScreen(instr[3],instr[4])
                    pen.Rect(x1,y1,x2,y2)
                if instr[0]=='line':
                    x1,y1=self.ToScreen(instr[1],instr[2])
                    x2,y2=self.ToScreen(instr[3],instr[4])
                    pen.Line(x1,y1,x2,y2)
                if instr[0]=='lines':
                    vertices=[]
                    for i in range(1,len(instr),2):
                        (x,y)=self.ToScreen(instr[i],instr[i+1])
                        vertices.append(x)
                        vertices.append(y)
                    pen.Lines(vertices)
                if instr[0]=='polygon':
                    vertices=[]
                    for i in range(1,len(instr),2):
                        (x,y)=self.ToScreen(instr[i],instr[i+1])
                        vertices.append(x)
                        vertices.append(y)
                    pen.Polygon(vertices)
                if instr[0]=='text':
                    x,y=self.ToScreen(instr[2],instr[3])
                    pen.Text(instr[1],x,y)

        def Add(self,instr):
            self.instructions.append(instr)
            return len(self.instructions)
