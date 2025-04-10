from direct.task.Task import TaskManager
import DefensePaths as defpath
from CollideObjectBase import *
from direct.showbase.Loader import *
from panda3d.core import NodePath
from panda3d.core import Vec3

class Orbiter(SphereCollideObject):
    numOrbits = 0
    velo = 0.005
    cloudTimer = 240

    def __init__(self, loader: Loader, taskMgr: TaskManager, modelPath: str, parentNode: NodePath, nodeName: str, scaleVec: Vec3, texPath: str, centralObject: PlacedObject, orbitRad: float, orbitType: str, staringAt: Vec3):
        super(Orbiter, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0,0,0), 3.2)
        self.taskMgr = taskMgr
        self.orbitType = orbitType
        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.orbitObject = centralObject
        self.orbitR = orbitRad
        self.staringAt = staringAt
        Orbiter.numOrbits += 1

        self.cloudClock = 0
        self.taskFlag = "Traveler-" + str(Orbiter.numOrbits)
        taskMgr.add(self.Orbit, self.taskFlag)
    
    def Orbit(self, task):
        if self.orbitType == "MLB":
            posVec = defpath.BaseballSeams(task.time * Orbiter.velo, self.numOrbits, 2.0)
            self.modelNode.setPos(posVec * self.orbitR + self.orbitObject.modelNode.getPos())
        
        elif self.orbitType == "Cloud":
            if self.cloudClock < Orbiter.cloudTimer:
                self.cloudClock += 1
                
            else:
                self.cloudClock = 0
                posVec = defpath.Cloud()
                self.modelNode.setPos(posVec * self.orbitR + self.orbitObject.modelNode.getPos())

        self.modelNode.lookAt(self.staringAt.modelNode)
        return task.cont