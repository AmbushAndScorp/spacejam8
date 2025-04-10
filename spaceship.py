from direct.showbase.Loader import *
from CollideObjectBase import *
from panda3d.core import NodePath
from panda3d.core import Vec3
from direct.task import Task
from typing import Callable
from bullets import Missile
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import TransparencyAttrib
from panda3d.core import CollisionTraverser
from panda3d.core import CollisionHandlerEvent
from direct.interval.LerpInterval import LerpFunc
from direct.particles.ParticleEffect import ParticleEffect
import re

class Spaceship (SphereCollideObject):
    def __init__(self, traverser: CollisionTraverser, loader: Loader, modelPath: str, parentNode: NodePath, nodeName: str, texPath: str, posVec: Vec3, scaleVec: float, manager: Task, accept: Callable[[str, Callable], None]):
        # setting up the player's collision, model, position, texture, and scale, plus making stuff equal to other stuff so everything else works
        super(Spaceship, self).__init__(loader, modelPath, parentNode, nodeName, Vec3(0,0,0), 1)
        self.render = parentNode
        self.modelNode.reparentTo(parentNode)
        self.loader = loader
        self.accept = accept
        self.modelNode.setPos(posVec)
        self.modelNode.setScale(scaleVec)
        self.modelNode.setName(nodeName)
        tex = loader.loadTexture(texPath)
        self.modelNode.setTexture(tex, 1)
        self.taskManager = manager

        # some base stuff for the score system
        self.scoreTrack = 0
        self.scoreStr = "Score: " + str(self.scoreTrack)

        # the stuff the missiles needs
        self.missileBay = 1 
        self.currBaySize = 1
        self.reloadTime = 0.25
        self.fireSwapCount = True
        self.missileDist = 4000
        self.taskManager.add(self.CheckIntervals, 'checkMissiles', 34)

        self.boostDelay = 15
        self.boostTime = 5
        self.boostSpeed = 10
        self.thrustSpeed = 5

        # enabling movement, firing, hud, and particles
        self.keyBinds()
        self.EnableHUD()
        self.SetParticles()

        # missile particles
        self.cntExplode = 0
        self.expoldeInterval = {}
        self.traverser = traverser
        self.handler = CollisionHandlerEvent()
        self.handler.addInPattern('into')
        self.accept('into', self.HandleInto)
    
    # heads up display activation
    def EnableHUD(self):
        self.hud = OnscreenImage("Assets/Hud/Reticle3b.png", pos = Vec3(0,0,0), scale = 0.1)
        self.hud.setTransparency(TransparencyAttrib.MAlpha)
        self.fireMode = OnscreenImage("Assets/Hud/Single.png", pos = Vec3(-0.6,0,-0.9), scale = 0.1)
        self.fireMode.setTransparency(TransparencyAttrib.MAlpha)
        self.bayStatus = OnscreenImage("Assets/Hud/loaded.png", pos = Vec3(0.6,0,-0.9), scale = 0.1)
        self.bayStatus.setTransparency(TransparencyAttrib.MAlpha)
        self.scoreDisplay = OnscreenText(text = self.scoreStr, pos=(-0.6,0.9), scale=0.07, fg=(243, 15, 252, 1))
        self.speedDisplay = OnscreenText(text = "Boost Ready", pos=(0.6,0.9), scale = 0.07,fg=(243, 15, 252, 1))

    # updating the score
    def UpdateScore(self):
        self.scoreDisplay.destroy()
        self.scoreStr = "Score: " + str(self.scoreTrack)
        self.scoreDisplay = OnscreenText(text = self.scoreStr, pos=(0,0.9), scale=0.07, fg=(243, 15, 252, 1))
    
    def keyBinds(self):
        # all bindings for movement
        self.accept('space', self.Thrust, [1])
        self.accept('space-up', self.Thrust, [0])
        self.accept('a', self.LeftTurn, [1])
        self.accept('a-up', self.LeftTurn, [0])
        self.accept('d', self.RightTurn, [1])
        self.accept('d-up', self.RightTurn, [0])
        self.accept('w', self.LookUp, [1])
        self.accept('w-up', self.LookUp, [0])
        self.accept('s', self.LookDown, [1])
        self.accept('s-up', self.LookDown, [0])
        self.accept('arrow_left', self.RollLeft, [1])
        self.accept('arrow_left-up', self.RollLeft, [0])
        self.accept('arrow_right', self.RollRight, [1])
        self.accept('arrow_right-up', self.RollRight, [0])
        self.accept('arrow_up', self.RollUp, [1])
        self.accept('arrow_up-up', self.RollUp, [0])
        self.accept('arrow_down', self.RollDown, [1])
        self.accept('arrow_down-up', self.RollDown, [0])

        # the attack button 
        self.accept('f', self.Fire)

        # swap firing mode
        self.accept('q', self.swapFire, [1])

        self.accept('e', self.SpeedBoost, [1])

    def SpeedBoost(self, keydown):
        #print("boost")
        self.speedDisplay.destroy()
        self.speedDisplay = OnscreenText(text = "Boosting", pos=(0.6,0.9), scale = 0.07,fg=(243, 15, 252, 1))
        self.thrustSpeed = self.boostSpeed
        self.taskManager.doMethodLater(self.boostTime, self.resetSpeed, 'boost-switch')
    
    def resetSpeed(self, task):
        if task.time > self.boostDelay:
            self.thrustSpeed = 5
            #print("you slow")
            self.speedDisplay.destroy()
            self.speedDisplay = OnscreenText(text = "Boost Ready", pos=(0.6,0.9), scale = 0.07,fg=(243, 15, 252, 1))
            return Task.done
        elif task.time <= self.boostDelay:
            #print("slow")
            self.speedDisplay.destroy()
            self.speedDisplay = OnscreenText(text = "Boost Recharging", pos=(0.6,0.9), scale = 0.07,fg=(243, 15, 252, 1))
            self.thrustSpeed = 5
            return Task.cont
    
    # the following is a lot of functions to make the movement actually move
    def Thrust(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyThrust, 'forward-thrust') 
        else:
            self.taskManager.remove('forward-thrust')

    def ApplyThrust(self, task):
        self.thrustRate = self.thrustSpeed
        traj = self.render.getRelativeVector(self.modelNode, Vec3.forward())
        traj.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + traj * self.thrustRate)

        return Task.cont
    
    def LeftTurn(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyLeftTurn, 'turn-left')
        else:
            self.taskManager.remove('turn-left')
    
    def ApplyLeftTurn(self, task):
        rate = .5
        self.modelNode.setH(self.modelNode.getH() + rate)
        return Task.cont
    
    def RightTurn(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyRightTurn, 'turn-right')
        else:
            self.taskManager.remove('turn-right')
    
    def ApplyRightTurn(self, task):
        rate = .5
        self.modelNode.setH(self.modelNode.getH() - rate)
        return Task.cont
    
    def LookUp(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyLookUp, 'look-up')
        else:
            self.taskManager.remove('look-up')
    
    def ApplyLookUp(self, task):
        rate = .5
        self.modelNode.setP(self.modelNode.getP() + rate)
        return Task.cont
    
    def LookDown(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyLookDown, 'look-down')
        else:
            self.taskManager.remove('look-down')
    
    def ApplyLookDown(self, task):
        rate = .5
        self.modelNode.setP(self.modelNode.getP() - rate)
        return Task.cont
    
    def RollLeft(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyRollLeft, 'left-roll')
        else:
            self.taskManager.remove('left-roll')
    
    def ApplyRollLeft(self, task):
        rate = 20
        traj = self.render.getRelativeVector(self.modelNode, Vec3.left())
        traj.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + traj * rate)
        return Task.cont
    
    def RollRight(self, keyDown):
        if keyDown:
            self.taskManager.add(self.ApplyRollRight, 'right-roll')
        else:
            self.taskManager.remove('right-roll')
    
    def ApplyRollRight(self, task):
        rate = 20
        traj = self.render.getRelativeVector(self.modelNode, Vec3.right())
        traj.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + traj * rate)
        return Task.cont
    
    def RollUp(self, keydown):
        if keydown:
            self.taskManager.add(self.ApplyRollUp, 'up-roll')
        else:
            self.taskManager.remove('up-roll')
    
    def ApplyRollUp(self, task):
        rate = 20
        traj = self.render.getRelativeVector(self.modelNode, Vec3.up())
        traj.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + traj * rate)
        return Task.cont
    
    def RollDown(self, keydown):
        if keydown:
            self.taskManager.add(self.ApplyRollDown, 'down-roll')
        else:
            self.taskManager.remove('down-roll')
    
    def ApplyRollDown(self, task):
        rate = 20
        traj = self.render.getRelativeVector(self.modelNode, Vec3.down())
        traj.normalize()
        self.modelNode.setFluidPos(self.modelNode.getPos() + traj * rate)
        return Task.cont
    
    # all the functions the player needs to make sure the missile goes off
    def Fire(self):
        if self.missileBay == 2:
            self.missileBay -= 1
            travRate = self.missileDist
            aim = self.render.getRelativeVector(self.modelNode, Vec3.forward())
            aim.normalize()
            fireSol = aim * travRate
            inFront = aim * 150
            travec = fireSol + self.modelNode.getPos()
            name = 'Missile' + str(Missile.missileCount)
            posVec = self.modelNode.getPos() + inFront
            currMissile = Missile(self.loader, 'Assets/Phaser/phaser.egg', self.render, name, posVec, 4.0)

            self.missileBay -= 1
            travRate2 = self.missileDist
            aim2 = self.render.getRelativeVector(self.modelNode, Vec3.forward())
            aim2.normalize()
            fireSol2 = aim * travRate2
            inFront = aim * 80
            travec2 = fireSol2 + self.modelNode.getPos()
            name2 = 'Missile' + str(Missile.missileCount)
            posVec2 = self.modelNode.getPos() + inFront
            currMissileBuddy = Missile(self.loader, 'Assets/Phaser/phaser.egg', self.render, name2, posVec2, 4.0)

            self.traverser.addCollider(currMissile.collisionNode, self.handler)
            Missile.Intervals[name] = currMissile.modelNode.posInterval(2.0, travec, startPos = posVec, fluid = 1)
            Missile.Intervals[name2] = currMissileBuddy.modelNode.posInterval(2.0, travec2, startPos = posVec2, fluid = 1)
            Missile.Intervals[name].start()
            Missile.Intervals[name2].start()
            self.bayStatus.setImage("Assets/Hud/empty.png")
            self.bayStatus.setTransparency(TransparencyAttrib.MAlpha)

        elif self.missileBay == 1:
            travRate = self.missileDist
            aim = self.render.getRelativeVector(self.modelNode, Vec3.forward())
            aim.normalize()
            fireSol = aim * travRate
            inFront = aim * 150
            travec = fireSol + self.modelNode.getPos()
            self.missileBay -= 1
            name = 'Missile' + str(Missile.missileCount)
            posVec = self.modelNode.getPos() + inFront
            currMissile = Missile(self.loader, 'Assets/Phaser/phaser.egg', self.render, name, posVec, 4.0)
            self.traverser.addCollider(currMissile.collisionNode, self.handler)
            Missile.Intervals[name] = currMissile.modelNode.posInterval(2.0, travec, startPos = posVec, fluid = 1)
            Missile.Intervals[name].start()
            self.bayStatus.setImage("Assets/Hud/empty.png")
            self.bayStatus.setTransparency(TransparencyAttrib.MAlpha)

        else:
            if not self.taskManager.hasTaskNamed('reload'):
                #print("starting reload")
                self.taskManager.doMethodLater(0, self.Reload, 'reload')
        
        return Task.cont
            
    def Reload(self, task):
        if task.time > self.reloadTime:
            self.missileBay = self.currBaySize
            #print("reload complete")
            self.bayStatus.setImage("Assets/Hud/loaded.png")
            self.bayStatus.setTransparency(TransparencyAttrib.MAlpha)
            return Task.done
        elif task.time <= self.reloadTime:
            #print("reload proceeding")
            self.bayStatus.setImage("Assets/Hud/reload.png")
            self.bayStatus.setTransparency(TransparencyAttrib.MAlpha)
            return Task.cont
        if self.missileBay > self.currBaySize:
            self.missileBay = self.currBaySize
    
    def CheckIntervals(self, task):
        for i in Missile.Intervals:
            if not Missile.Intervals[i].isPlaying():
                Missile.cNodes[i].detachNode()
                Missile.fireModels[i].detachNode()

                del Missile.Intervals[i]
                del Missile.fireModels[i]
                del Missile.cNodes[i]
                del Missile.collisionSolids[i]
                #print (i + " has reached the end of the fire solution")
                break
        return Task.cont
    
    def swapFire(self, keydown):
        if self.fireSwapCount == True:
            if keydown:
                self.taskManager.add(self.burstFire, 'swappage burst')
            else:
                self.taskManager.remove('swappage burst')
            self.fireSwapCount = False
        else:
            if keydown:
                self.taskManager.add(self.singleFire, 'swappage single')
            else:
                self.taskManager.remove('swappage single')
            self.fireSwapCount = True
    
    def burstFire(self, task):
        self.missileBay = 2
        self.currBaySize = 2
        self.reloadTime = 0.75
        self.fireMode.setImage("Assets/Hud/Burst (1).png")
        self.fireMode.setTransparency(TransparencyAttrib.MAlpha)
        #print("Burst fire active")
        if not self.taskManager.hasTaskNamed('reload'):
            #print("starting reload")
            self.taskManager.doMethodLater(0, self.Reload, 'reload')
    
    def singleFire(self, task):
        self.missileBay = 1
        self.currBaySize = 1
        self.reloadTime = 0.25
        self.fireMode.setImage("Assets/Hud/Single.png")
        self.fireMode.setTransparency(TransparencyAttrib.MAlpha)
        #print("single fire active")
        if not self.taskManager.hasTaskNamed('reload'):
            #print("starting reload")
            self.taskManager.doMethodLater(0, self.Reload, 'reload')

    # causing the explosions from when a missile hits an object
    def HandleInto(self, entry):
        fromNode = entry.getFromNodePath().getName()
        #print("fromNode: " + fromNode)
        intoNode = entry.getIntoNodePath().getName()
        #print("intoNode: " + intoNode)

        intoPos = Vec3(entry.getSurfacePoint(self.render))

        tempVar = fromNode.split('_')
        #print("tempVar: " + str(tempVar))
        shooter = tempVar[0]
        #print("shooter: " + str(shooter))
        tempVar = intoNode.split('-')
        #print("tempVar1: " + str(tempVar))
        tempVar = intoNode.split('_')
        #print("tempVar2: " + str(tempVar))
        victim = tempVar[0]
        #print("victim: " + str(victim))

        pattern = r'[0-9]'
        strippedStr = re.sub(pattern, '', victim)

        if (strippedStr=="Drone" or "Planet" in strippedStr or strippedStr=="Station" or "Drone" in strippedStr or "Station" in strippedStr):
            #print(victim, ' hit at ', intoPos)
            self.DestroyObject(victim, intoPos)
        
        #print(shooter + " IS DONE")
        Missile.Intervals[shooter].finish()
    
    def DestroyObject(self, hitID, hitPos):
        nodeID = self.render.find(hitID)
        nodeID.detachNode()
        if ("Planet" in hitID or "Station" in hitID):
            self.scoreTrack -= 1000
        elif ("Drone" in hitID):
            self.scoreTrack += 100
        
        self.UpdateScore()

        self.explodeNode.setPos(hitPos)
        self.Explode()
    
    def Explode(self):
        self.cntExplode += 1
        name = "particles-" + str(self.cntExplode)
        self.expoldeInterval[name] = LerpFunc(self.ExplodeLight, duration = 4.0)
        self.expoldeInterval[name].start()
    
    def ExplodeLight(self, t):
        if t == 1.0 and self.explodeEffect:
            self.explodeEffect.disable()
        elif t == 0:
            self.explodeEffect.start(self.explodeNode)
    
    def SetParticles(self):
        base.enableParticles() # this isn't an error, it just thinks it is but it lets the particle system be used
        self.explodeEffect = ParticleEffect()
        #self.explodeEffect.loadConfig("Assets/Part-Efx/SP21-explosionIII.ptf") # still don't know why this errors out
        self.explodeEffect.setScale(20)
        self.explodeNode = self.render.attachNewNode('ExplosionEffects')