
import cv2
from ultralytics import YOLO
import numpy as np
import pandas as pd
import math
import os
import perspective

def calc_center(mask):
    M = cv2.moments(mask)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    center = cX,cY
    return center

def order(image,centers,compass):
    y,x,_ = image.shape
    y/=2
    x/=2
    angles = np.array([])
    order = np.array([])
    pi = np.pi

    # Calculo dos ângulos
    for center in centers:
        deltaX=center[0]-x
        deltaY=center[1]-y
        angle= np.arctan(deltaY/deltaX)

        # Quadrante 1
        if(deltaY<0 and deltaX>0):
            angle = angle*(-1)
            print('Q1:',angle*180/pi)

        # Quadrante 2
        elif(deltaY<0 and deltaX<0):
            angle = pi-angle
            print('Q2:',angle*180/pi)
        
        # Quadrante 3
        elif(deltaY>0 and deltaX<0):
            angle = angle+pi
            print('Q3:',angle*180/pi)
        
        # Quadrante 4
        elif(deltaY>0 and deltaX>0):
            angle = angle*(-1)+2*pi
            print('Q4:',angle*180/pi)
        

        angles = np.append(angles,angle)
    orderAux = np.argsort(angles)

    angleRef = np.abs(angles[orderAux]-compass)
    angleIndex = int(np.argmin(angleRef))

    slice_1 = orderAux[angleIndex:]
    slice_2 = orderAux[0:angleIndex]

    order = np.concatenate((slice_1,slice_2))
 
    return order

def calc_diameter(mask):
    area = cv2.contourArea(mask)
    diameter = round(math.sqrt((area*4)/(math.pi)),2)
    #print('diametro: ',diameter)
    return diameter

def segment():
    # Load the YOLOv8 model
    root = os.path.dirname(os.path.abspath(__file__))
    weighstPath = os.path.join(root,'../weights/best.onnx')
    imagePath = os.path.join(root,'../test.png')

    model = YOLO(weighstPath,task='segment')
    results = model(imagePath)
    image = cv2.imread(imagePath)
    #image = cv2.resize(image, (740,740), interpolation = cv2.INTER_AREA)
    #results = model(image)
    diameters = np.array([])
    centers = np.array([[]])
    maskAux = []

    for result in results:
        for i in range(len(result)):
            mask = result[i].masks.xy
            mask = np.array(mask, np.int32)

            diameter = calc_diameter(mask)
            diameters = np.append(diameters,diameter)

            center = np.array(calc_center(mask))
            centers = np.append(centers,center) if not centers.any() else np.vstack([centers,center])

            maskAux.append(mask)

    # Encontrando o indice do diametro máximo 


    d_max_index = np.argmax(diameters)
    d_max = np.array(diameters[d_max_index])
    d_max_mask = maskAux[d_max_index]

    #remove d_max
    maskAux.pop(d_max_index)
    centers = np.delete(centers,d_max_index,axis=0)

    angle = 1.047
    holes_order = order(image,centers,angle)
    holes_order_list = holes_order.tolist()

    #Order Masks
    maskAux = [maskAux[i] for i in holes_order_list]
    maskAux.append(d_max_mask)

    for i,mask in enumerate(maskAux):
        center = calc_center(mask)
        #print(center)
        text_center = None
        if i < (len(maskAux)-1):
            text_center = int(center[0])-10,int(center[1])+10
        text = str(i)#+': '+str(diameters[i])
        annotated_frame = cv2.drawContours(image,mask,-1,(0,255,255),4)
        annotated_frame = cv2.putText(image,text,text_center ,cv2.FONT_HERSHEY_SIMPLEX,1,(0, 255, 0),2,cv2.LINE_AA )
    #annotated_frame=cv2.flip(perspective.six_points_transform(image,centers),1)
    
    cv2.imshow('teste',annotated_frame)
    cv2.waitKey(0)    

    return annotated_frame,diameters,True

if __name__ =='__main__':
    # root = os.path.dirname('WRLSegmentationScreen.py')
    # print(root)
    segment()