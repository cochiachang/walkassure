const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const message = document.getElementById('overlay-text');
const ctx = canvas.getContext('2d');
let videoSource = undefined
let sound

//--------------影像取得相關

function gotDevices(deviceInfos) {
    //console.log(deviceInfos)
    deviceInfos.forEach(deviceInfo => {
        if (deviceInfo.kind == "videoinput") {
            //console.log(deviceInfo)
            videoSource = deviceInfo.deviceId
        }
    });
}

function gotStream(stream) {
    window.stream = stream;
    videoElement.srcObject = stream;
    return navigator.mediaDevices.enumerateDevices();
}
let txt_mapping = {
    no_crosswalk: "畫面中沒有斑馬線",
    one_crosswalk: "前方有一個斑馬線",
    multi_crosswalk: "前方有多個斑馬線",
    start_crosswalk: "開始偵測斑馬線方向",
    unknow_direction: "斑馬線在你的未知方向",
    clock1_direction: "斑馬線在你的1點鐘方向",
    clock2_direction: "斑馬線在你的2點鐘方向",
    clock3_direction: "斑馬線在你的3點鐘方向",
    clock12_direction: "斑馬線在你的12點鐘方向",
    clock11_direction: "斑馬線在你的11點鐘方向",
    clock10_direction: "斑馬線在你的10點鐘方向",
    clock9_direction: "斑馬線在你的9點鐘方向",
    near_crosswalk: "斑馬線在附近",
    far_crosswalk: "斑馬線在遠方",
    wrong_direction: "你偏離了斑馬線",
    back_clock1_direction: "請往1點鐘方向返回",
    back_clock2_direction: "請往2點鐘方向返回",
    back_clock10_direction: "請往10點鐘方向返回",
    back_clock11_direction: "請往11點鐘方向返回",
    obstacle: "前方有",
    person: "行人",
    bicycle: "腳踏車",
    car: "汽車",
    motorcycle: "摩托車",
    bus: "公車",
    truck: "卡車",
    cat: "貓",
    dog: "狗",
    umbrella: "雨傘",
    handbag: "背包",
    traffic_red: "現在紅綠燈狀態為紅燈",
    traffic_green: "現在紅綠燈狀態為綠燈",
    traffic_unknow: "現在紅綠燈狀態為未偵測到",
    end_crosswalk: "斑馬線已結束",
    no_obstacle: "障礙物已離開"
}
window.onload = () => {
    navigator.mediaDevices.enumerateDevices().then(gotDevices).then(init).catch(handleError);
    sound = new Howl({
        src: ['sound.mp3'],
        sprite: {
            no_crosswalk: [0, 2300],
            one_crosswalk: [2500, 3000],
            multi_crosswalk: [5500, 3000],
            start_crosswalk: [8500, 3300],
            unknow_direction: [12000, 3500],
            clock1_direction: [15500, 3000],
            clock2_direction: [18500, 4000],
            clock3_direction: [22500, 4000],
            clock12_direction: [25500, 4000],
            clock11_direction: [29500, 4000],
            clock10_direction: [33500, 3500],
            clock9_direction: [37500, 3500],
            near_crosswalk: [41000, 2500],
            far_crosswalk: [43000, 2500],
            wrong_direction: [45800, 2500],
            back_clock1_direction: [48000, 3500],
            back_clock2_direction: [52000, 3000],
            back_clock10_direction: [55000, 3700],
            back_clock11_direction: [59000, 3500],
            obstacle: [63000, 1200],
            person: [65000, 1000],
            bicycle: [66000, 1500],
            car: [68000, 1000],
            motorcycle: [69500, 2000],
            bus: [71500, 1500],
            truck: [73000, 1000],
            cat: [74500, 1200],
            dog: [75500, 1200],
            umbrella: [77000, 1000],
            handbag: [78000, 1200],
            traffic_red: [80000, 3000],
            traffic_green: [83000, 3500],
            traffic_unknow: [87000, 4000],
            end_crosswalk: [91000, 2800],
            no_obstacle: [94000, 2500]
        }
    });

    sound.on('load', function () {
        loadSettingsFromCookies();
    });

    sound.on('end', function(){
        if(current_msg.length > 0){
            let next = current_msg.shift()
            sound.play(next)
        }
    });

    document.getElementById('rate').addEventListener('input', function () {
        setCookie('rateSetting', this.value, 30);
        sound.rate(1 + parseInt(this.value) * 0.1)
    });

    /*document.getElementById('switch').addEventListener('change', function () {
        setCookie('switchSetting', this.checked, 30);
    });*/
}

async function init() {
    try {
        //const stream = await navigator.mediaDevices.getUserMedia({ audio: false, video: { deviceId: videoSource ? { exact: videoSource } : undefined } });
        const stream = await navigator.mediaDevices.getUserMedia({ audio: false, video: { facingMode: 'environment' } });
        handleSuccess(stream);
    } catch (e) {
        handleError(e);
    }
}

function getRandomColor() {
    const randomColor = Math.floor(Math.random() * 16777215).toString(16);
    return "#" + ("000000" + randomColor).slice(-6);
}

//---------------websocket相關

function sendScreenToServer(ws, start_no_cross, is_in_crosswalk, previous_direction, remaining_crossings, detect_traffic) {
    let width = canvas.width;
    let height = canvas.height;
    let scaleFactor;
    if (width < height) {
        scaleFactor = 640 / width;
    } else {
        scaleFactor = 640 / height;
    }
    let newWidth = width * scaleFactor;
    let newHeight = height * scaleFactor;
    let tempCanvas = document.createElement('canvas');
    let tempCtx = tempCanvas.getContext('2d');

    tempCanvas.width = newWidth;
    tempCanvas.height = newHeight;
    tempCtx.drawImage(canvas, 0, 0, newWidth, newHeight);

    let message = {
        event: 'sned_image',
        data: tempCanvas.toDataURL("image/png"),
        start_no_cross: start_no_cross,
        is_in_crosswalk: is_in_crosswalk,
        previous_direction: previous_direction,
        remaining_crossings: remaining_crossings,
        detect_traffic: detect_traffic
    };
    ws.send(JSON.stringify(message));
}


current_msg = []
function connectWebSocket() {
    let wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = `${wsProtocol}//${window.location.hostname}:${window.location.port}/ws`;
    if (window.location.port == '') {
        wsUrl = `${wsProtocol}//${window.location.hostname}/ws`;
    }
    let ws = new WebSocket(wsUrl);
    let start_no_cross = 0
    let is_in_crosswalk = 0
    let previous_direction = 0
    let remaining_crossings = 0
    let interval_val = 0
    let last_crosswalk_detect = ""
    let last_crosswalk_direction = ""
    let last_traffic_light = ""
    let last_current_msg = []
    let last_obstacle = ""
    message.innerHTML = "連線中..."
    ws.onopen = function () {
        sendScreenToServer(ws, start_no_cross, is_in_crosswalk, previous_direction, remaining_crossings);
    };

    ws.onmessage = function (event) {
        let parsedObj = JSON.parse(event.data);
        if (parsedObj.event == "detect_result") {
            messages = JSON.parse(parsedObj.data);
            /*if (!document.getElementById('switch').checked) {
                messages.traffic_light = ""
            }*/
			messages.traffic_light = ""
            // 處理文字顯示
            obstacle = (messages.obstacle.length > 0) ? messages.obstacle.map(item => txt_mapping[item]).join(' '):""
            if(obstacle == "" && obstacle != last_obstacle){
                obstacle = txt_mapping["no_obstacle"]
            }
            let messageList = [
                txt_mapping[messages.crosswalk_detect],
                txt_mapping[messages.crosswalk_direction],
                txt_mapping[messages.traffic_light],
                obstacle
            ].filter(text => text && text.trim().length > 0);
            message.innerHTML = messageList.map(text => `<span>${text}</span>`).join('\n');

            // 處理音訊播放
            let needPlayTraffic = false;//messages.traffic_light != last_traffic_light && document.getElementById('switch').checked
            if (messages.crosswalk_detect != last_crosswalk_detect || messages.crosswalk_direction != last_crosswalk_direction || needPlayTraffic) {
                last_current_msg = current_msg
                current_msg = []
                sound.stop()
            }
            console.log(obstacle == txt_mapping["no_obstacle"] , obstacle != last_obstacle)

            if (obstacle != txt_mapping["no_obstacle"] && obstacle != last_obstacle) {
                current_msg.push(...messages.obstacle);
            }else if(obstacle == txt_mapping["no_obstacle"] && obstacle != last_obstacle){
                current_msg.push("no_obstacle")
            }
            if (messages.crosswalk_detect != last_crosswalk_detect) {
                current_msg.push(messages.crosswalk_detect)
            }
            if (messages.crosswalk_direction != last_crosswalk_direction) {
                current_msg.push(messages.crosswalk_direction)
            }
            if (needPlayTraffic) {
                current_msg.push(messages.traffic_light)
            }
            if(!sound.playing() && current_msg.length > 0){
                let next = current_msg.shift()
                sound.play(next)
            }

            // 回傳訊息
            last_crosswalk_detect = messages.crosswalk_detect
            last_crosswalk_direction = messages.crosswalk_direction
            last_traffic_light = messages.traffic_light
            last_obstacle = obstacle

            start_no_cross = parsedObj.start_no_cross;
            is_in_crosswalk = parsedObj.is_in_crosswalk;
            previous_direction = parsedObj.previous_direction;
            remaining_crossings = parsedObj.remaining_crossings;
			
			if(!sound.playing() && current_msg.length > 0){
				sendScreenToServer(ws, start_no_cross, is_in_crosswalk, previous_direction, remaining_crossings, false)//document.getElementById('switch').checked)
			}else{
				setTimeout(sendScreenToServer, 200, ws, start_no_cross, is_in_crosswalk, previous_direction, remaining_crossings, false)
			}
        }

        //console.log("Received from server:", event.data, previous_direction, remaining_crossings);
    };

    ws.onclose = function () {
        message.innerHTML = "與伺服器斷線"
        setTimeout(connectWebSocket, 1000);
        clearInterval(interval_val);
    };
}
function handleSuccess(stream) {
    connectWebSocket()
    video.srcObject = stream;
    video.addEventListener('play', () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        function drawFrame() {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            requestAnimationFrame(drawFrame);
        }
        drawFrame();
    });
}

function handleError(error) {
    alert(`getUserMedia error: ${error.name}`, error);
}

//----------------------設定介面操作相關

const rateSlider = document.getElementById('rate');
const decreaseLabel = document.getElementById('decrease');
const increaseLabel = document.getElementById('increase');

function closeOverlay() {
    document.getElementById("full-overlay").style.display = "none";
}

function openOverlay() {
    document.getElementById("full-overlay").style.display = "block";
}

rateSlider.addEventListener('input', function () {
    const currentValue = rateSlider.value;

    rateSlider.setAttribute('aria-valuenow', currentValue);

    let textDescription;
    if (currentValue <= 3) {
        textDescription = '慢';
    } else if (currentValue <= 7) {
        textDescription = '中';
    } else {
        textDescription = '快';
    }

    rateSlider.setAttribute('aria-valuetext', textDescription);
});

decreaseLabel.addEventListener('click', function () {
    if (rateSlider.value > rateSlider.min) {
        rateSlider.value -= 1;
        rateSlider.setAttribute('aria-valuenow', rateSlider.value);

        setCookie('rateSetting', rateSlider.value, 180);
        sound.rate(1 + parseInt(rateSlider.value) * 0.1)
    }
});

increaseLabel.addEventListener('click', function () {
    if (parseInt(rateSlider.value) < parseInt(rateSlider.max)) {
        rateSlider.value = parseInt(rateSlider.value) + 1; // 使用parseInt確保是數字加法，而不是字符串連接
        rateSlider.setAttribute('aria-valuenow', rateSlider.value);

        setCookie('rateSetting', rateSlider.value, 180);
        sound.rate(1 + parseInt(rateSlider.value) * 0.1)
    }
});


//-----------------------設定儲存相關

function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function loadSettingsFromCookies() {
    var rateSetting = getCookie('rateSetting');
    var switchSetting = getCookie('switchSetting');

    if (rateSetting) {
        document.getElementById('rate').value = rateSetting;
        try{
            sound.rate(1 + parseInt(rateSetting) * 0.1)
        }catch(e){}
    }
    if (switchSetting) {
        //document.getElementById('switch').checked = switchSetting === 'true'; // because cookie values are always strings
    }
}
