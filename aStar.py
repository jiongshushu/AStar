#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import logging

from collections import deque


def init_log(log_level=logging.INFO):
    format_str = '[%(levelname)s][%(asctime)s][tank_aStart]: %(message)s'
    logging.basicConfig(format=format_str, level=log_level,
                        datefmt='%Y-%m-%d %I:%M:%S')
    return logging.getLogger(__name__)


logger = init_log(logging.INFO)


class Grid(object):

    def __init__(self, parent=None, x=None, y=None):
        self.parent = parent
        self.x, self.y = x, y
        self.F = 100
        self.G = 0

    def isSameLine(self, grid):
        return self.x == grid.x or self.y == grid.y

    def get(self):
        return (self.x, self.y)


class GridList(object):

    def __init__(self):
        self.l = []
        self.exists = []

    def __len__(self):
        return len(self.l)

    def __contains__(self, point):
        return point in self.exists

    def __iter__(self):
        return self.l.__iter__()

    def get(self, point):
        i = self.exists.index(point)
        return self.l[i]

    def append(self, grid):
        self.l.append(grid)
        self.exists.append((grid.x, grid.y))

    def pop(self, i):
        grid = self.l.pop(i)
        self.exists.remove((grid.x, grid.y))
        return grid


class AStart(object):

    M = [
        # y ->
        [0, 0, 0],  # x
        [0, 1, 0],  # |
        [0, 0, 0],  # v
    ]

    blocks = {(1, 1)}

    mapVer = 1

    op, cl = GridList(), GridList()

    BLOCK_SYMBOL = 1

    pathCached = {}

    def __init__(self, M=None, blocks=None):
        if M:
            self.M = M
            self.blocks = set()

        self.xMin = -1
        self.yMin = -1
        self.xMax = len(self.M)
        self.yMax = len(self.M[0])

    def getNextStep(self, end=None, start=None):
        if (start, end, self.mapVer) not in self.pathCached:
            self.findPath(end, start)

        return self.pathCached[(start, end, self.mapVer)].pop()

    def findPath(self, end=None, start=None, output=False):
        if not start:
            start = (self.xMin+1, self.yMin+1)
        if not end:
            end = (self.xMax-1, self.yMax-1)

        if not output and (start, end, self.mapVer) in self.pathCached:
            return self.pathCached.get((start, end, self.mapVer)) or []

        startGrid = Grid(parent=None, x=start[0], y=start[1])
        endGrid = Grid(parent=None, x=end[0], y=end[1])
        curGrid = None

        self.op.l, self.cl.l = [startGrid], []
        self.op.exists, self.cl.exists = [start], []
        while len(self.op) > 0:
            curGrid = self.getMinFGrid()
            logger.debug("=============roop start==============")
            logger.debug("current grid[%s]", (curGrid.x, curGrid.y))

            if curGrid.x == endGrid.x and curGrid.y == endGrid.y:
                logger.info("arrived end grid")
                break

            self.getSurroundGrid(curGrid, endGrid)

            self.cl.append(curGrid)
            logger.debug("=============roop end==============")

        if curGrid.get() != endGrid.get():
            print("Error! can not find a path to the end: cur[%s], end[%s]" % (curGrid.get(), endGrid.get()))
            return 

        if output:
            self.printConsole(curGrid, startGrid, endGrid)
            return False
        else:
            path = list()
            while True:
                #logger.debug("Print Path: cur[%s], start[%s]", curGrid.get(), startGrid.get())
                if (curGrid.x == startGrid.x and curGrid.y == startGrid.y) or not curGrid.parent:
                    break
                path.append((curGrid.x, curGrid.y))
                curGrid = curGrid.parent
            self.pathCached[(start, end, self.mapVer)] = path
            return path
 

    def printConsole(self, curGrid, startGrid, endGrid):
        print("Find Path Result: start[%s], end[%s]", startGrid.get(), endGrid.get())
        print("==========map=============")
        for x in self.M:
            for y in x:
                print("%d, " % y, end="")
            print()
        print("==========map=============")

        print("==========path=============")
        while True:
            #logger.debug("Print Path: cur[%s], start[%s]", curGrid.get(), startGrid.get())
            if (curGrid.x == startGrid.x and curGrid.y == startGrid.y) or not curGrid.parent:
                print("(%d, %d)" % (curGrid.x, curGrid.y))
                break

            print("(%d, %d)" % (curGrid.x, curGrid.y))
            curGrid = curGrid.parent
        print("==========path=============")


    def getMinFGrid(self):
        minF, num = 100000000, 0
        for i, g in enumerate(self.op):
            if g.F > minF:
                continue
            minF, num = g.F, i

        return self.op.pop(num)

    def getSurroundGrid(self, curGrid, endGrid):
        for i in range(-1, 2):
            for j in range(-1, 2):
                x = curGrid.x + i
                y = curGrid.y + j
                if (x, y) == (curGrid.x, curGrid.y):
                    logger.debug(
                        "Surround point[%s] not calc: equal current", (x, y))
                    continue
                if (x, y) in self.cl:
                    logger.debug(
                        "Surround point[%s] not calc: already in close list", (x, y))
                    continue
                if not self.isSafeGrid(x, y):
                    self.cl.append(curGrid)
                    logger.debug(
                        "Surround point[%s] not calc: not safe", (x, y))
                    continue
                if (x, y) in self.op:
                    logger.debug(
                        "Surround point[%s]: already in open list", (x, y))
                    grid = Grid(parent=curGrid, x=x, y=y)
                    grid.F = self.calcF(grid, endGrid)
                    existGrid = self.op.get((x, y))
                    logger.debug(
                        "Calc F result: point[%s], old_G[%d], old_F[%d], new_G[%d], new_F[%d]", (x, y), existGrid.G, grid.F, existGrid.G, grid.F)
                    if grid.G <= existGrid.G:
                        existGrid.G = grid.G
                        existGrid.F = grid.F
                        existGrid.parent = grid.parent
                else:
                    logger.debug("Surround point[%s]: need new calc", (x, y))
                    grid = Grid(parent=curGrid, x=x, y=y)
                    grid.F = self.calcF(grid, endGrid)
                    logger.debug(
                        "Calc F result: point[%s], G[%d], F[%d]", (x, y), grid.G, grid.F)
                    self.op.append(grid)

    def calcF(self, grid, endGrid):
        return self.calcG(grid) + self.calcH(grid, endGrid)

    def calcG(self, grid):
        grid.G = grid.parent.G
        if grid.isSameLine(grid.parent):
            grid.G += 10
        else:
            grid.G += 20
        return grid.G

    def calcH(self, grid, endGrid):
        return abs(grid.x - endGrid.x) + abs(grid.y - endGrid.y)

    def isSafeGrid(self, x, y):
        # x in safe range
        if x <= self.xMin or x >= self.xMax:
            return False

        # y in safe range
        if y <= self.yMin or y >= self.yMax:
            return False

        # Grid is not block
        if self.M[x][y] == self.BLOCK_SYMBOL:
            return False

        # Safe
        return True


def main():
    import json
    import time
    M = []
    with open("map.json", "r") as f:
        M = json.loads(f.read())
    star = AStart(M=M)
    for _ in range(2):
        t1 = time.time()
        path = star.findPath(output=False)
        t2 = time.time()
        t = t2 - t1
        print("[%f]" % t)


if __name__ == "__main__":
    main()
