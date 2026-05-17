import asyncio
import websockets
import json
import argparse
import random
import colorsys

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import map
import unit
import status

class AI:
    def __init__(self, role, kwargs={}):
        self.role = role
        self.mapData = None
        self.unitData = None
        self.mode = kwargs.get("mode",None)
        self.setup_moves = []
        self.statusData = None
    def euclideanDistanceToOpfor(self, hex):
        xA = hex.x_grid
        yA = hex.y_grid
        closest = None
        closest_dist = float('inf')
        if not self.unitData.units():
            return float('inf')
        for target in self.unitData.units():
            if target.faction == self.role or target.ineffective or not target.hex:                 continue
            xB = target.hex.x_grid
            yB = target.hex.y_grid
            dist = map.gridDistance(xA,yA,xB,yB)
            if dist < closest_dist:
                closest_dist = dist
                closest = target
        return closest_dist
    def euclideanDistanceToCities(self, hex):
        if self.role=="red":
            opfor = "blue"
        else:
            opfor = "red"
        xA = hex.x_grid
        yA = hex.y_grid
        closest_dist = float('inf')
        if self.statusData.ownerD:
            for city_id in self.statusData.ownerD:
                xB = self.mapData.hexIndex[city_id].x_grid
                yB = self.mapData.hexIndex[city_id].y_grid
                dist = map.gridDistance(xA,yA,xB,yB)
                if dist < closest_dist:
                    closest_dist = dist  
        return closest_dist
    def colorsFromDists(self, dists):
        max_dist = float('-inf')
        min_dist = float('inf')
        for hex_id in dists:
            max_dist = max( dists[hex_id], max_dist)
            min_dist = min( dists[hex_id], min_dist)
        # Set color
        colors = {}
        for hex_id in dists:
            sat = 0.5
            val = 1.0
            if max_dist == min_dist:
                hue = 0
            else:
                hue = (dists[hex_id] - min_dist) / (max_dist - min_dist) * 250 / 360
            rgb = tuple(round(x * 255) for x in colorsys.hsv_to_rgb(hue,sat,val))
            color = '#'
            for i in rgb:
                s = str(hex(i))
                if len(s)==3:
                    color += '0' + s[-1:]
                else:
                    color += s[-2]
            colors[hex_id] = color
        return colors 
    def getPosture(self):
        if self.mode=="pass":
            return "defense"
        elif self.mode=="agg":
            return "attack"
        str_red = 0
        str_blue = 0
        for unt in self.unitData.units():
            if unt.ineffective:
                continue
            if unt.faction=="red":
                str_red += unt.currentStrength
            elif unt.faction=="blue":
                str_blue += unt.currentStrength
        if self.role=="red" and str_red>=str_blue:
            posture = "attack"
        elif self.role=="blue" and str_blue>=str_red:
            posture = "attack"
        else:
            posture = "defense"
        return posture       
    def _scoreHex(self,hex,posture):
        score = float('inf')
        dist1 = self.euclideanDistanceToOpfor(hex)
        dist2 = self.euclideanDistanceToCities(hex)
        if posture=="attack" and dist1<float('inf'):
            score = dist1
        if dist2<float('inf'):
            if score<float('inf'):
                score += dist2
            else:
                score = dist2
        return score
    def takeBestAction(self):
        dists = {}
        posture = self.getPosture()
        for unt in self.unitData.units():
            if unt.faction == self.role and unt.canMove and not unt.ineffective:
                fireTargets = unt.findFireTargets(self.unitData)
                if fireTargets:
                    # Shoot at a random target, if we have at least one
                    return {"type":"action", "action":{"type":"fire", "source":unt.uniqueId, "target":random.choice(fireTargets).uniqueId}}
                currentHexScore = self._scoreHex(unt.hex,posture)
                moveTargets = unt.findMoveTargets(self.mapData, self.unitData)
                if moveTargets:
                    closest_dist = float('inf')
                    best_hex = None
                    for hex in moveTargets:
                        score = self._scoreHex(hex,posture)
                        dists[hex.id] = score
                        if score < closest_dist:
                            closest_dist = score
                            best_hex = hex
                    if closest_dist < currentHexScore:
                        colors = self.colorsFromDists(dists)
                        return {"type":"action", "action":{"type":"move", "mover":unt.uniqueId, "destination":best_hex.id, }, "debug":{"colors":colors}}
        return { "type":"action", "action":{"type":"pass"} }
    def getSetupMoves(self):
        posture = self.getPosture()
        setup_hexes = self.mapData.getSetupHexes(self.role)
        scored_hexes = [(hex,self._scoreHex(hex,posture)) for hex in setup_hexes]
        random.shuffle(scored_hexes)
        scored_hexes.sort( key=lambda x: x[1], reverse=True )
        #print([(h.id,s) for (h,s) in scored_hexes])
        moves = []
        moves.append( {"type":"pass"} )
        occ = self.unitData.occupancy
        for unt in self.unitData.getFaction(self.role):
            hex, _ = scored_hexes.pop()
            # If hex occupied, exchange, otherwise move
            if hex.id in occ and len(occ[hex.id]):
                occupier_id = occ[hex.id][0].uniqueId
                moves.append( {"type":"setup-exchange", "mover":unt.uniqueId, "friendly":occupier_id} )
            else:
                moves.append( {"type":"setup-move", "mover":unt.uniqueId, "destination":hex.id} )
        return moves
    def process(self, message, response_fn=None):
        msgD = json.loads(message)
        ######### Change this function to create new AIs ########  
        if msgD['type'] == "parameters":
            self.param = msgD['parameters']
            self.mapData = map.MapData()
            self.unitData = unit.UnitData()
            map.fromPortable(self.param['map'], self.mapData)
            unit.fromPortable(self.param['units'], self.unitData, self.mapData)
            responseD = { "type":"role-request", "role":self.role }
        elif msgD['type'] == 'observation':
            obs = msgD['observation']
            self.statusData = status.Status.fromPortable(obs["status"], self.param, self.mapData)      
            if not obs['status']['isTerminal'] and obs['status']['onMove'] == self.role:
                if obs['status']['setupMode']:
                    if not self.setup_moves:
                        self.setup_moves = self.getSetupMoves()
                    move = self.setup_moves.pop()
                    obj = {"type":"action", "action":move}
                    return json.dumps(obj)
                else:
                    self.statusData = status.Status.fromPortable(obs["status"], self.param, self.mapData)
                    for unitObs in obs['units']:
                        uniqueId = unitObs['faction'] + " " + unitObs['longName']
                        un = self.unitData.unitIndex[ uniqueId ]
                        un.partialObsUpdate( unitObs, self.unitData, self.mapData )
                    responseD = self.takeBestAction()
            else:
                responseD = None
        elif msgD['type'] == 'reset':
            responseD = None
        if responseD:
            return json.dumps(responseD)
 

async def client(ai, uri):
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            print(f"Message received by AI over websocket: {message[:100]}")
            result = ai.process(message)
            if result:
                await websocket.send( result )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("faction")
    parser.add_argument("--uri")
    args = parser.parse_args()
    
    ai = AI(args.faction)
    uri = args.uri
    if not uri:
        uri = "ws://localhost:9999"
    asyncio.get_event_loop().run_until_complete(client(ai, uri))
    
 