from direct.showbase.Loader import *
from panda3d.core import NodePath
from panda3d.core import Vec3
from CollideObjectBase import *
from direct.interval.IntervalGlobal import Sequence

class Wanderer(SphereCollideObject):
    numWanders = 0

    def __init__(self, loader: Loader, modelPath: str, parentNode: NodePath, modelName: str, scaleVec: Vec3, texPath: str, staringAt: Vec3):
        super(Wanderer, self).__init__(loader, modelPath, parentNode, modelName, Vec3(0,0,0), 3.2)

        self.modelNode.setScale(scaleVec)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.staringAt = staringAt
        Wanderer.numWanders += 1

        posInterval0 = self.modelNode.posInterval(20, Vec3(300, 6000, 500), startPos = Vec3(-900,7000,200))
        posInterval1 = self.modelNode.posInterval(20, Vec3(700, -2000, 100), startPos = Vec3(300, 6000, 500))
        posInterval2 = self.modelNode.posInterval(20, Vec3(0, -900, -1400), startPos = Vec3(700, -2000, 100))
        posInterval3 = self.modelNode.posInterval(20, Vec3(-900,7000,200), startPos = Vec3(0, -900, -1400))

        if Wanderer.numWanders % 2 == 0:
            posInterval0 = self.modelNode.posInterval(30, Vec3(0,-10000,-40), startPos = Vec3(0,0,0))
            posInterval1 = self.modelNode.posInterval(20, Vec3(50, -5000, -40), startPos = Vec3(0,-10000,-40))
            posInterval2 = self.modelNode.posInterval(20, Vec3(25, -2500, -10), startPos = Vec3(50, -5000, -40))
            posInterval3 = self.modelNode.posInterval(20, Vec3(0,0,0), startPos = Vec3(25, -2500, -10))

        self.travelRoute = Sequence(posInterval0, posInterval1, posInterval2, posInterval3, name = "Traveler")
        self.travelRoute.loop()