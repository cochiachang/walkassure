WalkAssure
====

### Project Objectives:
* The main project objective is to develop a iOS mobile app that helps visually impaired individuals navigate safely and independently, especially when crossing roads.
* The app will use AI image recognition technology to identify safe crossing areas and obstacles.
* It will provide real-time information about the surroundings and enhance the user experience.
![screenshot-1](https://raw.githubusercontent.com/cochiachang/walkassure/main/images/screenshot-1.png)
![screenshot-2](https://raw.githubusercontent.com/cochiachang/walkassure/main/images/screenshot-2.jpg)

### User Interviews and Insights:
* Interviews were conducted with visually impaired individuals, including those with partial vision and full blindness.
* Different types of visual impairments and their specific needs were identified.
* Challenges include difficulties in transportation, identifying objects, and using technology effectively.

### Technical Choices:
* Instance Segmentation ([Ultralytics YOLOv8l-seg](https://github.com/ultralytics/ultralytics))
* OpenCV for crosswalk angle detection and obstacle detection
* Voice prompts, with adjustable voice speed in real-time.

### Training Data for Zebra Crossing Detection:
* GitHub open data ([Crosswalks-Detection-using-YOLO](https://github.com/xN1ckuz/Crosswalks-Detection-using-YOLO)) / Self-labeling / 713 images
* All training data opensource in [Roboflow Open datasets](https://universe.roboflow.com/project-wdkej/crosswalk2-jqjh4)
* Self-captured photos and videos (designed for different daytime, nighttime, crowd, weather, and regional variations) / Self-labeling

### Quantitative Results 
|                |Box               |Mask   |
|----------------|------------------|-----  |
|Precision       |99.9%             |97.4%  |        
|Recall          |99.3%             |99.3%  |       
|mAP50           |99.5%             |99.5%  |
|mAP50-95        |97.4%             |96.1%  |

![result](https://raw.githubusercontent.com/cochiachang/walkassure/main/images/results.png)
![predict status](https://raw.githubusercontent.com/cochiachang/walkassure/main/images/pred.jpg)

### Install
Create a clean environment
```
conda create --name cleanenv python=3.8.1
conda activate cleanenv
```
Install dependencies
```
pip install ultralytics aiohttp
```
or install from requirements.txt
```
pip install -r requirements.txt
```
### License 
This work is under GNU GENERAL PUBLIC LICENSE, check LICENSE file for details. All rights reserved to [Ultralytics](https://github.com/ultralytics/ultralytics) for the YOLO model.
