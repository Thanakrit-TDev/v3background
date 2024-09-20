from flask import Flask, render_template, Response, jsonify, request,send_file,stream_with_context
import requests
import cv2
import json
import os
import fnmatch
import time
from datetime import datetime
import time
import numpy as np
import threading

import mysql.connector
from mysql.connector import Error

from io import BytesIO

import serial.tools.list_ports
import serial

from tensorflow.keras.models import load_model
import numpy as np
from tensorflow.keras.preprocessing import image

import shutil
from flask_cors import CORS

connection = None

app = Flask(__name__)
# getlist camera -------
def returnCameraIndexes():
    # checks the first 10 indexes.
    index = 0
    arr = []
    i = 10
    while i > 0:
        try:
            cap = cv2.VideoCapture(index)
            if cap.read()[0]:
                arr.append(index)
                cap.release()
            index += 1
            i -= 1
        except:
            continue
    return arr
# print('camera =>',returnCameraIndexes())
listcamera = returnCameraIndexes()
# ----------------------

# global varible
status_pesent_detect = {"qrdata":0,"hight":0}

if(len(listcamera)>=0):
    camera = cv2.VideoCapture(listcamera[0])  # Use 0 for web camera

frame_global = None
def nothing(x):
    pass

@app.route("/setting", methods=["POST"])
def set_value():
    data = request.get_json()  # Get the JSON data sent in the request
    # load json file -------------------------------------
    file_path = os.path.join(os.path.dirname(__file__), 'settingbuf.json')
    with open(file_path, 'r') as file:
        data_load = json.load(file)
    # add json file to databese --------------------------
    data_load[data['time_save']] = {
        "name": data['tube_name_setting_str'],
        "tube_hight": float(data['tube_hight_str']),
        "tube_diameter": float(data['tube_diameter_str']),
        "px":int(data['tube_px_str']),
        "mm":int(data['tube_mm_str'])
    }
    with open(file_path, 'w') as file:
        json.dump(data_load, file)
    #----------------------------------------------------
    response = {
        "stsave": True,
    }

    status_res = requests.get('http://127.0.0.1:5000/sync_setting_from_database')

    return jsonify(response), 200

@app.route("/loadsetting", methods=["GET"])
def loadsetting():
    file_path = os.path.join(os.path.dirname(__file__), 'settingbuf.json')
    with open(file_path, 'r') as file:
        data_load = json.load(file)
    response = {
        "data": data_load,
    }
    return jsonify(response), 200

@app.route("/usesettingthis", methods=["POST"])
def usesettingthis():
    data_from_app = request.get_json()
    #load json
    file_path = os.path.join(os.path.dirname(__file__), 'settingbuf.json')
    with open(file_path, 'r') as file:
        data_load = json.load(file)
    buf_data_json = data_load[data_from_app['old_id']]
    #sort json
    del data_load[data_from_app['old_id']]
    data_load[data_from_app['new_id']] = buf_data_json
    #dump json
    with open(file_path, 'w') as file:
        json.dump(data_load, file)
    response = {
        "data": "data_load",
    }
    return jsonify(response), 200

@app.route("/deletesettingthis", methods=["POST"])
def deletesettingthis():
    data_from_app = request.get_json()
    #load json
    file_path = os.path.join(os.path.dirname(__file__), 'settingbuf.json')
    with open(file_path, 'r') as file:
        data_load = json.load(file)
    buf_data_json = data_load[data_from_app['old_id']]
    #sort json
    del data_load[data_from_app['old_id']]
    # data_load[data_from_app['new_id']] = buf_data_json
    #dump json
    with open(file_path, 'w') as file:
        json.dump(data_load, file)
    response = {
        "data": "data_load",
    }

    status_res = requests.get('http://127.0.0.1:5000/sync_setting_from_database')

    return jsonify(response), 200

@app.route("/command_send", methods=["POST"])
def command_send():
    data_from_app = request.get_json()
    print("datafrom app ",data_from_app['command'])
    datasend = {'command':data_from_app['command']}
    # try:
    response = requests.post('http://127.0.0.1:2000/costom_command', json=datasend)
    print(response)
    # except requests.exceptions.RequestException as e:
    #     pass
    response = {
        "data": "data_load",
    }
    return jsonify(response), 200

@app.route("/list_camera", methods=["GET"])
def list_camera():
    global listcamera
    response = {
        "data": listcamera,
    }
    return jsonify(response), 200

listcamera_use = 0
@app.route("/use_camera_now", methods=["POST"])
def use_camera_now():
    global listcamera_use
    global camera
    data_from_app = request.get_json()
    camera = cv2.VideoCapture(int(data_from_app['camera']))
    response = {
        "st": 'ok',
    }
    listcamera_use = int(data_from_app['camera'])
    return jsonify(response), 200

@app.route("/status_chacking", methods=["GET"])
def status_chacking():
    global status_pesent_detect
    response = {
        "status_detect": status_pesent_detect,
    }
    return jsonify(response), 200

# @app.route("/set_status_plasma", methods=["GET"])
# def set_status_plasma():
#     global status_pesent_detect
#     status_pesent_detect = 'plasma'
#     response = {
#         "status_detect": status_pesent_detect,
#     }
#     return jsonify(response), 200

# @app.route("/set_status_qrcode", methods=["GET"])
# def set_status_qrcode():
#     global status_pesent_detect
#     status_pesent_detect = 'qrcode'
#     response = {
#         "status_detect": status_pesent_detect,
#     }
#     return jsonify(response), 200

# @app.route("/set_status_wait", methods=["GET"])
# def set_status_wait():
#     global status_pesent_detect
#     status_pesent_detect = 'wait'
#     response = {
#         "status_detect": status_pesent_detect,
#     }
#     return jsonify(response), 200



def find_h_files(directory):
    h_files = []
    file_path = os.path.join(os.path.dirname(__file__), directory)
    for root, dirnames, filenames in os.walk(file_path):
        for filename in fnmatch.filter(filenames, '*.h5'):
            # h_files.append(os.path.join(root, filename))
            h_files.append(filename)

    return h_files
@app.route("/get_list_model_inmycomputer", methods=["GET"])
def get_list_model_inmycomputer():
    list_model_for_send = []
    directory_path = 'modellist'
    h_files = find_h_files(directory_path)
    file_path = os.path.join(os.path.dirname(__file__), 'modellist\\listmode.json')
    with open(file_path, 'r') as file:
        data_load = json.load(file)
    for i in data_load["model_list_all"]:
        # data_load[i]
        for i2 in h_files:
            if(data_load["model_list_all"][i]['filename'] == i2):
                list_model_for_send.append(i)
    # print('i => ',list_model_for_send)
    response = {
        "model_version_inmycomputer": list_model_for_send,
    }
    return jsonify(response), 200


@app.route("/get_model_from_internet", methods=["GET"])
def get_model_from_internet():
    url = "http://210.246.215.145:1234/get_model_from_internet"
    response = requests.get(url)
    response = response.json()

    file_path = os.path.join(os.path.dirname(__file__), 'modellist/listmode.json')
    with open(file_path, 'w') as json_file:
        json.dump(response, json_file)

    # print(response)
    return jsonify(response), 200

# load use now model in mypc ---------------
version_model_usenow = ''
file_path = os.path.join(os.path.dirname(__file__), 'modellist/nowusemodel.json')
with open(file_path, 'r') as json_file:
    data_load_from_now_model = json.load(json_file)
    version_model_usenow = data_load_from_now_model['use_now_model']
# print(data_load_from_now_model)


@app.route("/use_model_in_mycomputer", methods=["POST"])
def use_model_in_mycomputer():
    global version_model_usenow
    data_from_app = request.get_json()
    print("model choose =>",data_from_app['model_v'])
    file_path = os.path.join(os.path.dirname(__file__), 'modellist/nowusemodel.json')
    with open(file_path, 'w') as json_file:
        data_keep = {'use_now_model':data_from_app['model_v']}
        data_load_from_now_model = json.dump(data_keep, json_file)
        version_model_usenow = data_from_app['model_v']

    st_model = "use_ok"
    response = {
        "model_st": st_model,
    }
    return jsonify(response), 200


def sum_static_history(start_date,end_date,mode):
    sum_his_lost = {}
    sum_his_true = {}
    souse_data = {}
    data_all = {}
    try:
        start_timestamp = int(start_date)
        end_timestamp = int(end_date)
        date1 = datetime.fromtimestamp(start_timestamp).date().strftime("%Y-%m-%d")
        date2 = datetime.fromtimestamp(end_timestamp).date().strftime("%Y-%m-%d")
        db = mysql.connector.connect(
                host="210.246.215.145",
                user="root",
                password="OKOEUdI1886*",
                database="plasma"
            )
        cursor = db.cursor()
        # query = """SELECT * FROM `graph`WHERE `time` BETWEEN %s AND %s;"""
        query = """SELECT * FROM `graph` WHERE `time` BETWEEN %s AND %s ORDER BY `time` ASC;"""
        cursor.execute(query, (date1, date2))
        results = cursor.fetchall()
        
        if(mode == "Day"):
            count = 0
            for data in results:
                sum_his_lost[f"{data[0]}"] = data[2]
                sum_his_true[f"{data[0]}"] = data[1]
                souse_data[count] = count
                count+=1
                # print(data[0])

        if(mode == "Week"):
            count = 0
            T_sum = 0
            F_sum = 0
            c_sou = 0
            for data in results:
                count += 1
                F_sum = F_sum + data[2]
                T_sum = T_sum + data[1]
                if count % 7 == 0 or results[-1][0] == data[0]:
                    sum_his_lost[f"{data[0]}"] = F_sum
                    sum_his_true[f"{data[0]}"] = T_sum
                    T_sum = 0
                    F_sum = 0
                    souse_data[c_sou] = c_sou
                    c_sou+=1

    
        if(mode == "Month"):
            m_now = results[0][0].month #0
            T_sum = 0
            F_sum = 0
            for data in results:
                if(data[0].month != m_now or results[-1][0] == data[0]):
                    m_now = data[0].month
                    sum_his_lost[f"{data[0]}"] = F_sum
                    sum_his_true[f"{data[0]}"] = T_sum
                    T_sum = 0
                    F_sum = 0
                else:
                    F_sum = F_sum + data[2]
                    T_sum = T_sum + data[1]
# #  'Day', 'Week', 'Month', 'Year'
        if(mode == "Year"):
            m_now = results[0][0].year #0
            T_sum = 0
            F_sum = 0
            count_numder = 0
            for data in results:
                count_numder += 1
                # if(data[0].year != m_now or results[-1][0] == data[0]):
                if(data[0].year != m_now or len(results) == count_numder):
                    m_now = data[0].year
                    sum_his_lost[f"{data[0]}"] = F_sum
                    sum_his_true[f"{data[0]}"] = T_sum
                    T_sum = 0
                    F_sum = 0
                else:
                    F_sum = F_sum + data[2]
                    T_sum = T_sum + data[1]
        
        cursor.close()
        db.close()
    except (ValueError, TypeError, KeyError) as e:
        pass

    # print(mode)
    data_all["false_tube"] = sum_his_lost
    data_all["true_tube"] = sum_his_true
    data_all["souse"] = souse_data

    return data_all


@app.route("/get_history_for_graph", methods=["POST"])
def get_history_for_graph():
    data_from_app = request.get_json()
    
    # print(data_from_app['mode'])
    
    res_data = sum_static_history(data_from_app["start"],data_from_app['end'],data_from_app['mode'])
    # print(res_data)
    response = {
        "hisreturn": res_data,
    }
    
    # response = {
    #     "hisreturn": {"false_tube":{"1/2":50},"true_tube":{"1/2":13}},
    # }
    return jsonify(response), 200

@app.route("/download_model_from_internet", methods=["POST"])
def download_model_from_internet():
    # time.sleep(5)
    data_from_app = request.get_json()
    # send to server "download_model":
    version_download = data_from_app["download_model"]
    url = 'http://210.246.215.145:1234/download_model_from_internet'
    data = {
        "download_model": version_download,
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        file_path = os.path.join(os.path.dirname(__file__), f'modellist/tube({version_download}).h5')
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print("File downloaded successfully.")
    else:
        print(f"Failed to download file. Status code: {response.status_code}")

    response = {
        "st_loadModel":True
    }
    return jsonify(response), 200


@app.route("/sync_setting_from_database", methods=["GET"])
def sync_setting_from_database():
    file_path = os.path.join(os.path.dirname(__file__), 'settingbuf.json')
    with open(file_path, 'r') as file:
        data_load = json.load(file)
    data_for_save = {
        "data_sync":data_load
    }
    url = 'http://210.246.215.145:1234/sync_setting_from_database'
    response = requests.post(url, json=data_for_save)
    response = {
        "st_sync": True,
    }
    return jsonify(response), 200


@app.route("/save_setting_from_database", methods=["GET"])
def save_setting_from_database():
    url = 'http://210.246.215.145:1234/save_setting_from_database'
    response = requests.get(url)
    response = response.json()
    file_path = os.path.join(os.path.dirname(__file__), 'settingbuf.json')
    with open(file_path, 'w') as file:
        json.dump(response["data_sync"], file)
    response = {
        "st_sync": True,
    }
    return jsonify(response), 200


@app.route("/get_log", methods=["GET"])
def get_log():
    global connection,json
    try:
        connection = mysql.connector.connect(
            host='210.246.215.145',
            database='plasma',
            user='root',
            password='OKOEUdI1886*',
            connection_timeout=3
        )
        # print("testStatus ",connection.is_connected())
        if connection.is_connected():
            db_Info = connection.get_server_info()
            print("Connected to MySQL Server version", db_Info)
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            record = cursor.fetchone()
            cursor.execute("SELECT * FROM log ORDER BY timestamp DESC LIMIT 5")
            rows = cursor.fetchall()
            # print("from log server : ",rows)
            return jsonify(rows),200

    except Error as e:
        # data_list = []
        # file_path = os.path.join(os.path.dirname(__file__), 'offline_log\\offline_log.json')
        # with open(file_path, 'r') as file:
        #     data_load = json.load(file)
        return jsonify([["no internet","False","no internet",0,0,0,0.0,"\rno internet"]]), 200

    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
    #         print("MySQL connection is closed")


@app.route("/test_log_status_true", methods=["GET"])
def test_log_status_true():
    try:
        now_time = int(time.time())
        db = mysql.connector.connect(
            host="210.246.215.145",
            user="root",
            password="OKOEUdI1886*",
            database="plasma"
        )

        cursor = db.cursor()
        rr = {}
        rr[str(now_time)] = {"Tube": "True", "Datetime": now_time}
        for key, value in rr.items():
            timestamp_value = int(key)
            data = value["Tube"]
            datetime_value = value["Datetime"]
            cursor.execute("""
            INSERT INTO log (timestamp, data, datetime)
            VALUES (FROM_UNIXTIME(%s), %s, FROM_UNIXTIME(%s))
            """, (timestamp_value, data, datetime_value))
        db.commit()
        cursor.close()
        db.close()
        return jsonify(rr), 200
    
    except:
        data_list = []
        file_path = os.path.join(os.path.dirname(__file__), 'offline_log\\offline_log.json')
        with open(file_path, 'r') as file:
            data_load = json.load(file)

        dt_object = datetime.fromtimestamp(now_time)
        formatted_date = dt_object.strftime('%a, %d %b %Y %H:%M:%S GMT')
        data_load.insert(0,[f"{formatted_date}","True",f"{formatted_date}"])

        with open(file_path, 'w') as file:
            json.dump(data_load, file)

        return jsonify([f"{formatted_date}","True",f"{formatted_date}"]),200


@app.route("/test_log_status_false", methods=["GET"])
def test_log_status_false():
    try:
        now_time = int(time.time())
        db = mysql.connector.connect(
            host="210.246.215.145",
            user="root",
            password="OKOEUdI1886*",
            database="plasma"
        )
        cursor = db.cursor()
        rr = {}
        rr[str(now_time)] = {"Tube": "False", "Datetime": now_time}
        for key, value in rr.items():
            timestamp_value = int(key)
            data = value["Tube"]
            datetime_value = value["Datetime"]
            cursor.execute("""
            INSERT INTO log (timestamp, data, datetime)
            VALUES (FROM_UNIXTIME(%s), %s, FROM_UNIXTIME(%s))
            """, (timestamp_value, data, datetime_value))
        db.commit()
        cursor.close()
        db.close()
        return jsonify(rr), 200
    except:
        data_list = []
        file_path = os.path.join(os.path.dirname(__file__), 'offline_log\\offline_log.json')
        with open(file_path, 'r') as file:
            data_load = json.load(file)

        dt_object = datetime.fromtimestamp(now_time)
        formatted_date = dt_object.strftime('%a, %d %b %Y %H:%M:%S GMT')
        data_load.insert(0,[f"{formatted_date}","False",f"{formatted_date}"])

        with open(file_path, 'w') as file:
            json.dump(data_load, file)

        return jsonify([f"{formatted_date}","False",f"{formatted_date}"]),200


# zone display_feed ------------------------------------------------
app_2 = Flask(__name__)
# CORS(app_2)
img = None
running = True
def nothing(x):
    pass


file_path = os.path.join(os.path.dirname(__file__), 'set_detect_yellow.json')
with open(file_path, 'r') as file:
    data_load = json.load(file)
h_min = int(data_load['h_min'])
h_max = int(data_load['h_max'])
s_min = int(data_load['s_min'])
s_max = int(data_load['s_max'])
v_min = int(data_load['v_min'])
v_max = int(data_load['v_max'])
brightness = int(data_load['brightness'])
contrast = int(data_load['contrast'])
saturation_boost = int(data_load['saturation_boost'])
range_detect = int(data_load['range_detect'])

cal_px = 0
calh = 0

frame = None

@app_2.route("/Setting_realtime_mask", methods=["POST"])
def Setting_realtime_mask():
    global h_min,h_max,s_min,s_max,v_min,v_max,brightness,contrast,saturation_boost,range_detect
    data_from_app = request.get_json()

    h_min = int(data_from_app["Hue_Min"])
    h_max = int(data_from_app["Hue_Max"])
    s_min = int(data_from_app["Sat_Min"])
    s_max = int(data_from_app["Sat_Max"])
    v_min = int(data_from_app["Val_Min"])
    v_max = int(data_from_app["Val_MAX"])
    brightness = int(data_from_app["Brightness"])
    contrast = int(data_from_app["Contrast"])
    saturation_boost = int(data_from_app["Saturation"])
    range_detect = int(data_from_app["Range"])

    # print(data_from_app)
    return jsonify({"message": "Settings received successfully"}), 200

@app_2.route('/endprogram')
def endprogram():
    global running
    running = False
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "Server shutting down..."

def server_run():
    app_2.run('127.0.0.1', 2545, debug=False)

def server_run2():
    app.run(debug=False)

# zone core scaner read -------------------------------
app_3 = Flask(__name__)
@app_3.route("/found_comport", methods=["GET"])
def found_comport():
    # global ser_obj,ser_senser
    list_of_device = []
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return jsonify({"device": []}), 200
    for port in ports:
        list_of_device.append(port.device)
    return jsonify({"device": list_of_device}), 200

global_ser_scaner = None
@app_3.route("/connect_comport", methods=["POST"])
def connect_comport():
    global global_ser_scaner
    data_from_app = request.get_json()
    if(global_ser_scaner is not None):
        global_ser_scaner.close()
        global_ser_scaner = serial.Serial(data_from_app['device_name'], 115200, timeout=1)
    else:
        global_ser_scaner = serial.Serial(data_from_app['device_name'], 115200, timeout=1)
    return jsonify({"st": "ok"}), 200

# AI pr funecion -----------------
def upload_log(Mode,High,position,volume,diameter,qrdata):
    db = mysql.connector.connect(
        host="210.246.215.145",
        user="root",
        password="OKOEUdI1886*",
        database="plasma"
    )
    cursor = db.cursor()
    rr = {}
    rr[str(datetime.now().timestamp())] = {"Tube": f"{Mode}", "Datetime": datetime.fromtimestamp(datetime.now().timestamp())}
    for key, value in rr.items():
        timestamp_value = datetime.fromtimestamp(int(float(key))).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Converted Timestamp: {timestamp_value}")
        data = value.get("Tube")
        datetime_value = value.get("Datetime")
        if data is None or datetime_value is None:
            print(f"Missing data in value: {value}")
            continue  # Skip this iteration if data is missing
        # INSERT INTO log (timestamp, data, datetime)VALUES (%s, %s, %s)
        try:
            cursor.execute("""
            INSERT INTO log (timestamp, data, datetime, High, position, volume, diameter, qrdata) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (timestamp_value, data, datetime_value,High, position, volume, diameter, qrdata))
        except Exception as e:
            print(f"Failed to insert data: {e}")
            db.rollback()  # Rollback if there's an error
            continue
    try:
        db.commit()
        print("Database commit successful")
    except Exception as e:
        print(f"Commit failed: {e}")
    try:
        cursor.close()
        db.close()
        print("Database connection closed")
    except Exception as e:
        print(f"Failed to close the database: {e}")

High_setting_global = 33
position_setting_global = 33
volume_setting_global = 33
diameter_setting_global = 33
qrdata_setting_global = 'kuykuykuy'

image_in_process_detect = None
image_in_process_mask = None

now_model_not_compile = ''
model = None

def Ai_pr():
    global version_model_usenow
    global calh
    global cal_px
    global camera

    global dataQr_fromscaner #
    global High_setting_global #
    global position_setting_global #
    global volume_setting_global #
    global diameter_setting_global #
    global qrdata_setting_global #

    # global h_min
    # global h_max
    # global s_min
    # global s_max
    # global v_min
    # global v_max
    # global brightness
    # global contrast
    # global saturation_boost
    # global range_detect

    global image_in_process_detect
    global image_in_process_mask

    global listcamera_use
    global now_model_not_compile

    global model

    #load setting detect
    file_path = os.path.join(os.path.dirname(__file__), 'set_detect_yellow.json')
    with open(file_path, 'r') as file:
        data_load = json.load(file)
    h_min = int(data_load['h_min'])
    h_max = int(data_load['h_max'])
    s_min = int(data_load['s_min'])
    s_max = int(data_load['s_max'])
    v_min = int(data_load['v_min'])
    v_max = int(data_load['v_max'])
    brightness = int(data_load['brightness'])
    contrast = int(data_load['contrast'])
    saturation_boost = int(data_load['saturation_boost'])
    range_detect = int(data_load['range_detect'])

    # get setting now
    file_path = os.path.join(os.path.dirname(__file__), 'settingbuf.json')
    with open(file_path, 'r') as file:
        data_load = json.load(file)
    data_buf = []
    for i in data_load:
        data_buf.append(i)

    if(now_model_not_compile != version_model_usenow):
        file_path = os.path.join(os.path.dirname(__file__), f'modellist\\tube({version_model_usenow}).h5')
        model = load_model(file_path)    
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        now_model_not_compile = version_model_usenow

    camera_1 = cv2.VideoCapture(listcamera_use)
    # wite time 
    count_frame = 0
    while True:
        ret, frame = camera_1.read()
        if(count_frame >= 20):
            break
        count_frame += 1
        cv2.waitKey(1)

    # ret, frame = camera_1.read()
    if ret:
        # cv2.imshow('Captured Frame', frame)
        img_resized = cv2.resize(frame, (model.input_shape[1], model.input_shape[2]))
        image_for_train = frame.copy()
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)

        # img = image.load_img(img_path, target_size=(150, 150))  # ขนาดของภาพที่ใช้ตอนฝึกโมเดล
        img_array = image.img_to_array(img_rgb)
        img_array = np.expand_dims(img_array, axis=0)  # เพิ่มมิติสำหรับ batch
        img_array /= 255.0
        prediction = model.predict(img_array)
        print(f"Prediction: {prediction}")

        # prediction = [0.7]  # Replace this with your actual prediction logic
        good_path = os.path.join(os.path.dirname(__file__), "image_pr\\good")
        bad_path = os.path.join(os.path.dirname(__file__), "image_pr\\bad")
        os.makedirs(good_path, exist_ok=True)
        os.makedirs(bad_path, exist_ok=True)

        good_path_pr = os.path.join(os.path.dirname(__file__), "image_model_pr\\good")
        bad_path_pr = os.path.join(os.path.dirname(__file__), "image_model_pr\\bad")
        os.makedirs(good_path_pr, exist_ok=True)
        os.makedirs(bad_path_pr, exist_ok=True)

        # add data to image 
        brightness_1 = brightness - 50  # ปรับค่าให้เป็น -50 ถึง 50
        contrast_1 = contrast / 50.0  # ปรับค่าให้เป็น 0 ถึง 2.0
        
        frame = cv2.convertScaleAbs(frame, alpha=contrast_1, beta=brightness_1)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_boost, 0, 255)
        lower_yellow = np.array([h_min, s_min, v_min])
        upper_yellow = np.array([h_max, s_max, v_max])
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        rect_x1, rect_y1 = 200, 50
        rect_x2, rect_y2 = 450, 450
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        st_detect = False

        for contour in contours:
            if cv2.contourArea(contour) > range_detect:
                x, y, w, h = cv2.boundingRect(contour)
                if x >= rect_x1 and y >= rect_y1 and (x + w) <= rect_x2 and (y + h) <= rect_y2:
                    cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
                    calw = x + w
                    calh = y + h
                    cv2.rectangle(frame, (x, y), (calw, calh), (0, 0, 255), 2)
                    frame = cv2.putText(frame, f'P1:{y}', (calw + 10, y), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 255, 0), 1, cv2.LINE_AA)
                    frame = cv2.putText(frame, f'P2:{calh}', (calw + 10, calh), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (0, 255, 0), 1, cv2.LINE_AA)
                    po_w_box = y + int((calh - y) / 2)
                    cal_px = calh - y
                    frame = cv2.putText(frame, f'PW:{cal_px} Px', (calw + 10, po_w_box), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (255, 255, 0), 1, cv2.LINE_AA)
                    st_detect = True

        cv2.rectangle(frame, (rect_x1, rect_y1), (rect_x2, rect_y2), (255, 0, 0), 5)

        if(st_detect == False):
            cal_px = 0
        # conves px to mm
        h_mm_tube = int((int(data_load[max(data_buf)]['mm']) * cal_px) / int(data_load[max(data_buf)]['px']))
        diameter_mm = int((int(data_load[max(data_buf)]['mm']) * int(data_load[max(data_buf)]['tube_diameter'])) / int(data_load[max(data_buf)]['px']))

        High_setting_global = h_mm_tube
        diameter_setting_global = diameter_mm
        qrdata_setting_global = dataQr_fromscaner
        # cal start position 
        position_setting_global = calh
        # cal volume
        volume_setting_global = 3.14159 * ((diameter_mm/2) * (diameter_mm/2)) * h_mm_tube

        #-------------------------------------------------------------------------------------------------
        
        if prediction[0][0] > 0.5:
            print("Prediction: Good")
            frame = cv2.putText(frame, f'Good', (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 1, cv2.LINE_AA)
            file_path = good_path
            file_path_pr = good_path_pr
            upload_log(True, High_setting_global, position_setting_global, volume_setting_global, diameter_setting_global, qrdata_setting_global)

        if prediction[0][1] > 0.5:
            print("Prediction: Bad")
            frame = cv2.putText(frame, f'Bad', (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 1, cv2.LINE_AA)
            file_path = bad_path
            file_path_pr = bad_path_pr
            upload_log(False, High_setting_global, position_setting_global, volume_setting_global, diameter_setting_global, qrdata_setting_global)

        image_in_process_detect = frame
        image_in_process_mask = mask

        str_time_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f'{str_time_name}.jpg'
        full_path = os.path.join(file_path, file_name)
        try:
            cv2.imwrite(full_path, image_for_train)
            # print(f"Image saved as {full_path}")
        except Exception as e:
            print(f"Cannot save image: {e}")
        #for show pr model floder
        full_path_pr = os.path.join(file_path_pr, file_name)
        try:
            cv2.imwrite(full_path_pr, frame)
            # print(f"Image saved as1 {full_path_pr}")
            return 0
        except Exception as e:
            print(f"Cannot save image: {e}")

        # if cv2.getWindowProperty("Yellow Detection mask", cv2.WND_PROP_VISIBLE) > 0 or cv2.getWindowProperty("Yellow Detection", cv2.WND_PROP_VISIBLE) > 1:
        # camera_1.release()


dataQr_fromscaner = ''
data_return_to_app = {}
@app_3.route("/get_qr_and_plamamode", methods=["GET"])
def get_qr_and_plamamode():
    global global_ser_scaner,dataQr_fromscaner,cal_px,data_return_to_app,status_pesent_detect
    if(global_ser_scaner is not None):
        if(global_ser_scaner.is_open):
            global_ser_scaner.write(b'read_qr\n')

            dataQr_fromscaner = ''
            while True:
                if(dataQr_fromscaner != ""):
                    # data_return_to_app = {"qrdata":dataQr_fromscaner,"hight":High_setting_global}
                    # status_pesent_detect = {"qrdata":dataQr_fromscaner,"hight":High_setting_global}
                    break
            # Ai zone -------------------------
            Ai_pr()
            data_return_to_app = {"qrdata":dataQr_fromscaner,"hight":High_setting_global}
            status_pesent_detect = {"qrdata":dataQr_fromscaner,"hight":High_setting_global}
            # end -----------------------------
            # time.sleep(1)
    return jsonify({"st": "ok","qrdata":dataQr_fromscaner,"hight":High_setting_global}), 200

@app.route("/get_data_qr_plasma", methods=["GET"])
def get_data_qr_plasma():
    global data_return_to_app
    return jsonify(data_return_to_app), 200


def run_read_scan_qrcode():
    global global_ser_scaner,dataQr_fromscaner
    while True:
        if(global_ser_scaner is not None):
            if(global_ser_scaner.is_open):
                if global_ser_scaner and global_ser_scaner.in_waiting > 0:
                    line = global_ser_scaner.readline().decode('utf-8').rstrip()
                    print(f'Received: {line}')
                    dataQr_fromscaner = line
        else:
            time.sleep(0.1)

def run_server_comport():
    app_3.run('127.0.0.1', 3000, debug=False)

# zone run ai pre -------------------------------
app_4 = Flask(__name__)
keep_data_setting = [True,True,True]


def send_login(u,p):
    try:
        db = mysql.connector.connect(
                host="210.246.215.145",
                user="root",
                password="OKOEUdI1886*",
                database="plasma"
            )
        cursor = db.cursor()
        print(cursor)
        query = """SELECT * FROM account WHERE user = %s AND password = %s;"""
        cursor.execute(query, (u, p))
        results = cursor.fetchall()
        print(results)
        cursor.close()
        db.close()
        if(results[0][0] == u and results[0][1] == p):
            return jsonify({"st":True})
        else:
            return jsonify({"st":False})
    except:
        return jsonify({"st":False})

@app_4.route("/test_ai", methods=["GET"])
def test_ai():
    Ai_pr()
    return jsonify({"results":"oo"}), 200

@app_4.route("/login", methods=["POST"])
def get_data_from():
    data_from_app = request.get_json()
    print(data_from_app)
    
    status_res = requests.get('http://127.0.0.1:5000/sync_setting_from_database')

    return(send_login(data_from_app['t'],data_from_app['a'])),200

@app_4.route("/get_limit_bad_image", methods=["GET"])
def get_limit_bad_image():
    file_path = os.path.join(os.path.dirname(__file__), f'limit_image.json')
    with open(file_path, 'r') as file:
        data_load = json.load(file)
    
    st = True
    file_path = os.path.join(os.path.dirname(__file__), 'image_pr\\bad')
    files = os.listdir(file_path)
    jpg_bad = sum(1 for file in files if file.lower().endswith('.jpg'))

    file_path = os.path.join(os.path.dirname(__file__), 'image_pr\\good')
    files = os.listdir(file_path)
    jpg_good = sum(1 for file in files if file.lower().endswith('.jpg'))

    if jpg_bad > int(data_load['count']):
       st = True
    else:
        st = False
    data = {
        "limit_bad_image":{
            "st":st,
            "setlimit_image":int(data_load['count']),
            "image_pr_bad": jpg_bad,
            "image_pr_good": jpg_good
        }
    }
    return jsonify(data), 200

@app_4.route("/setting_limit_bad_image", methods=["POST"])
def setting_limit_bad_image():
    data_from_app = request.get_json()
    print(data_from_app['tube_mm_str'])
    file_path = os.path.join(os.path.dirname(__file__), f'limit_image.json')
    with open(file_path, 'w') as file:
        data = {
	        "count":data_from_app['tube_mm_str']
        }
        json.dump(data,file)
    return jsonify({"ok":"ok"}), 200


@app_4.route("/upload_All_to_pool", methods=["GET"])
def upload_All_to_pool():
    folder_path = os.path.join(os.path.dirname(__file__), 'image_pr\\good')
    url = 'http://210.246.215.145:1234/save_dataset_to_pool'
    json_data = {
        "pool": "good",
    }
    for image_name in os.listdir(folder_path):
        image_path = os.path.join(folder_path, image_name)
        if image_name.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            with open(image_path, 'rb') as img_file:
                files = {'file': img_file}
                data = {'json_data': json.dumps(json_data)}
                response = requests.post(url, files=files, data=data)
                # if response.status_code == 200:
                #     os.remove(image_path)

    folder_path = os.path.join(os.path.dirname(__file__), 'image_pr\\bad')
    url = 'http://210.246.215.145:1234/save_dataset_to_pool'
    json_data = {
        "pool": "bad",
    }
    for image_name in os.listdir(folder_path):
        image_path = os.path.join(folder_path, image_name)
        if image_name.endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            with open(image_path, 'rb') as img_file:
                files = {'file': img_file}
                data = {'json_data': json.dumps(json_data)}
                response = requests.post(url, files=files, data=data)
    return jsonify({"ok":"ok"}), 200

def run_ai_pre():
    app_4.run('127.0.0.1', 3500, debug=False)


app_test_vdo = Flask(__name__)

st_show_image = False
camera = None
def run_camara_real_time():
    global camera
    global st_show_image
    global listcamera_use
    start_frist = True
    end_stop = False

    global h_min, h_max, s_min, s_max, v_min, v_max, brightness, contrast, saturation_boost, range_detect

    while True:
        if(st_show_image):
            if(start_frist):
                cv2.namedWindow("Yellow Detection")
                cv2.createTrackbar("Hue Min", "Yellow Detection", h_min, 179, nothing)
                cv2.createTrackbar("Hue Max", "Yellow Detection", h_max, 179, nothing)
                cv2.createTrackbar("Sat Min", "Yellow Detection", s_min, 255, nothing)
                cv2.createTrackbar("Sat Max", "Yellow Detection", s_max, 255, nothing)
                cv2.createTrackbar("Val Min", "Yellow Detection", v_min, 255, nothing)
                cv2.createTrackbar("Val Max", "Yellow Detection", v_max, 255, nothing)
                cv2.createTrackbar("Brightness", "Yellow Detection", brightness, 100, nothing)
                cv2.createTrackbar("Contrast", "Yellow Detection", contrast, 100, nothing)
                cv2.createTrackbar("Saturation Boost", "Yellow Detection", saturation_boost, 10, nothing)
                cv2.createTrackbar("Range", "Yellow Detection", range_detect, 2000, nothing)
                camera = cv2.VideoCapture(listcamera_use)
                start_frist = False

            success, frame = camera.read()

            h_min = cv2.getTrackbarPos("Hue Min", "Yellow Detection")
            h_max = cv2.getTrackbarPos("Hue Max", "Yellow Detection")
            s_min = cv2.getTrackbarPos("Sat Min", "Yellow Detection")
            s_max = cv2.getTrackbarPos("Sat Max", "Yellow Detection")
            v_min = cv2.getTrackbarPos("Val Min", "Yellow Detection")
            v_max = cv2.getTrackbarPos("Val Max", "Yellow Detection")
            brightness = cv2.getTrackbarPos("Brightness", "Yellow Detection")
            contrast = cv2.getTrackbarPos("Contrast", "Yellow Detection")
            saturation_boost = cv2.getTrackbarPos("Saturation Boost", "Yellow Detection")
            range_detect = cv2.getTrackbarPos("Range", "Yellow Detection")

            if(success):
                brightness_1 = brightness - 50  # ปรับค่าให้เป็น -50 ถึง 50
                contrast_1 = contrast / 50.0  # ปรับค่าให้เป็น 0 ถึง 2.0
                frame = cv2.convertScaleAbs(frame, alpha=contrast_1, beta=brightness_1)

                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_boost, 0, 255)
                lower_yellow = np.array([h_min, s_min, v_min])
                upper_yellow = np.array([h_max, s_max, v_max])
                mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
                # Define ROI and process contours
                rect_x1, rect_y1 = 200, 50
                rect_x2, rect_y2 = 450, 450
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    if cv2.contourArea(contour) > range_detect:
                        x, y, w, h = cv2.boundingRect(contour)
                        if x >= rect_x1 and y >= rect_y1 and (x + w) <= rect_x2 and (y + h) <= rect_y2:
                            cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
                            calw = x + w
                            calh = y + h
                            cv2.rectangle(frame, (x, y), (calw, calh), (0, 0, 255), 2)
                            frame = cv2.putText(frame, f'P1:{y}', (calw + 10, y), cv2.FONT_HERSHEY_SIMPLEX,
                                                0.5, (0, 255, 0), 1, cv2.LINE_AA)
                            frame = cv2.putText(frame, f'P2:{calh}', (calw + 10, calh), cv2.FONT_HERSHEY_SIMPLEX,
                                                0.5, (0, 255, 0), 1, cv2.LINE_AA)
                            po_w_box = y + int((calh - y) / 2)
                            cal_px = calh - y
                            frame = cv2.putText(frame, f'PW:{cal_px} Px', (calw + 10, po_w_box), cv2.FONT_HERSHEY_SIMPLEX,
                                                0.5, (255, 255, 0), 1, cv2.LINE_AA)
                cv2.rectangle(frame, (rect_x1, rect_y1), (rect_x2, rect_y2), (255, 0, 0), 5)
                cv2.imshow("Yellow Detection mask",mask)
                cv2.imshow("Yellow Detection",frame)
                cv2.waitKey(1)
                if cv2.getWindowProperty("Yellow Detection mask", cv2.WND_PROP_VISIBLE) < 1:  # ตรวจจับการปิดหน้าต่าง
                    file_path = os.path.join(os.path.dirname(__file__), 'set_detect_yellow.json')
                    with open(file_path, 'w') as file:
                        data = {
                            "h_min":h_min,
                            "h_max":h_max,
                            "s_min":s_min,
                            "s_max":s_max,
                            "v_min":v_min,
                            "v_max":v_max,
                            "brightness":brightness,
                            "contrast":contrast,
                            "saturation_boost":saturation_boost,
                            "range_detect":range_detect
                        }
                        json.dump(data,file)
                    st_show_image = False
                    end_stop = True
                if cv2.getWindowProperty("Yellow Detection", cv2.WND_PROP_VISIBLE) < 1:  # ตรวจจับการปิดหน้าต่าง
                    file_path = os.path.join(os.path.dirname(__file__), 'set_detect_yellow.json')
                    with open(file_path, 'w') as file:
                        data = {
                            "h_min":h_min,
                            "h_max":h_max,
                            "s_min":s_min,
                            "s_max":s_max,
                            "v_min":v_min,
                            "v_max":v_max,
                            "brightness":brightness,
                            "contrast":contrast,
                            "saturation_boost":saturation_boost,
                            "range_detect":range_detect
                        }
                        json.dump(data,file)
                    st_show_image = False
                    end_stop = True
        else:
            if(end_stop):
                cv2.destroyAllWindows()
                camera.release()
                end_stop = False
            start_frist = True

@app_test_vdo.route('/video_feed_process_on')
def video_feed_process_on():
    global st_show_image
    st_show_image = True
    return jsonify({"feed_process_on":"ok"}),200

@app_test_vdo.route('/image_process_detect')
def image_process_detect():
    global image_in_process_detect
    if(image_in_process_detect is None):
        folder_path = os.path.join(os.path.dirname(__file__), 'image_pr\\image_no_last\\load.jpg')
        img = cv2.imread(folder_path)
    else:
        img = image_in_process_detect
    if img is None:
        return "No image available", 404
    _, jpeg = cv2.imencode('.jpg', img)
    jpeg_bytes = jpeg.tobytes()
    return Response(jpeg_bytes, mimetype='image/jpeg')

@app_test_vdo.route('/image_process_mask')
def image_process_mask():
    global image_in_process_mask
    if(image_in_process_mask is None):
        folder_path = os.path.join(os.path.dirname(__file__), 'image_pr\\image_no_last\\load.jpg')
        img = cv2.imread(folder_path)
    else:
        img = image_in_process_mask
    if img is None:
        return "No image available", 404
    _, jpeg = cv2.imencode('.jpg', img)
    jpeg_bytes = jpeg.tobytes()
    return Response(jpeg_bytes, mimetype='image/jpeg')

def run_vdo_only():
    app_test_vdo.run('127.0.0.1', 3501, debug=False)

if __name__ == '__main__':
    c1 = threading.Thread(target=run_vdo_only)
    c1.daemon = True
    c1.start()

    c2 = threading.Thread(target=server_run)
    c2.daemon = True
    c2.start()

    c3 = threading.Thread(target=server_run2)
    c3.daemon = True
    c3.start()

    c4 = threading.Thread(target=run_server_comport)
    c4.daemon = True
    c4.start()

    c5 = threading.Thread(target=run_read_scan_qrcode) # มีปัญหา
    c5.daemon = True
    c5.start()

    c6 = threading.Thread(target=run_ai_pre)
    c6.daemon = True
    c6.start()

    c7 = threading.Thread(target=run_camara_real_time) 
    c7.daemon = True
    c7.start()

    while True:
        time.sleep(1)