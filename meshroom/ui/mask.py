import cv2
import numpy as np
import os

from PySide2.QtCore import QObject, Slot


class Masking(QObject):   
    @Slot(str, 'QVariantList', float, int, int, str)
    def rectangle(self, imgPath, rectPos, scale, resolution, iterations, outputMask):
        img = cv2.imread(imgPath)
        originalSize = img.shape[:2]
        resizeFactor = resolution/100
        if resolution != 100:
            img = cv2.resize(img,None,fx=resizeFactor,fy=resizeFactor,interpolation=cv2.INTER_NEAREST)
         
        bgdModel = np.zeros((1,65), np.float64)
        fgdModel = np.zeros((1,65), np.float64)
         
        rect = tuple([ round((i/scale)*resizeFactor) for i in rectPos ])
        if rect[:1:-1] == img.shape[:2]:
            # If there are no background samples, this will throw error
            # So we just set it all to probably foreground and let the user mark the background
            mask = np.full(img.shape[:2], cv2.GC_PR_FGD, np.uint8)
        else:
            mask = np.zeros(img.shape[:2], np.uint8)
            cv2.grabCut(img,mask,rect,bgdModel,fgdModel,iterations,cv2.GC_INIT_WITH_RECT)

        cacheDir = os.path.dirname(outputMask)
        if not os.path.exists(cacheDir):
            os.mkdir(cacheDir)

        mask2 = np.zeros(mask.shape, np.uint8)
        mask2[mask == cv2.GC_BGD] = 0
        mask2[mask == cv2.GC_FGD] = 255
        mask2[mask == cv2.GC_PR_BGD] = 1
        mask2[mask == cv2.GC_PR_FGD] = 254

        if mask.shape == tuple(originalSize):
            cv2.imwrite(outputMask, mask2)
        else:
            cv2.imwrite(outputMask, cv2.resize(mask2,tuple(originalSize),interpolation=cv2.INTER_NEAREST))

    @Slot(str, str, float, int, int, str)
    def markings(self, imgPath, userMarkings, scale, resolution, iterations, outputMask):
        img = cv2.imread(imgPath)
        originalSize = img.shape[:2]
        resizeFactor = resolution/100
        if resolution != 100:
            img = cv2.resize(img,None,fx=resizeFactor,fy=resizeFactor,interpolation=cv2.INTER_NEAREST)
        
        markings = cv2.imread(userMarkings)
        oldMask = cv2.imread(outputMask, 0)
        height, width = img.shape[:2]
        marks = cv2.resize(markings,(width, height),interpolation=cv2.INTER_NEAREST)
        old = cv2.resize(oldMask,(width, height),interpolation=cv2.INTER_NEAREST)
        
        mask = np.zeros(img.shape[:2], np.uint8)
        mask[old == 0] = cv2.GC_BGD
        mask[old == 255] = cv2.GC_FGD
        mask[old == 1] = cv2.GC_PR_BGD
        mask[old == 254] = cv2.GC_PR_FGD
        mask[np.where((marks==[0,0,255]).all(axis=2))] = cv2.GC_BGD
        mask[np.where((marks==[255,0,0]).all(axis=2))] = cv2.GC_FGD
         
        bgdModel =  np.zeros((1,65), np.float64)
        fgdModel =  np.zeros((1,65), np.float64)
         
        cv2.grabCut(img,mask,None,bgdModel,fgdModel,iterations,cv2.GC_INIT_WITH_MASK)
         
        mask2 = np.zeros(mask.shape, np.uint8)
        mask2[mask == cv2.GC_BGD] = 0
        mask2[mask == cv2.GC_FGD] = 255
        mask2[mask == cv2.GC_PR_BGD] = 1
        mask2[mask == cv2.GC_PR_FGD] = 254

        if mask2.shape == tuple(originalSize):
            cv2.imwrite(outputMask, mask2)
        else:
            cv2.imwrite(outputMask, cv2.resize(mask2,tuple(originalSize),interpolation=cv2.INTER_NEAREST))

        
        
