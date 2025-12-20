// グローバル変数
let mediaRecorder;
let audioChunks = [];
let recordingStartTime;
let recordingInterval;
let currentAudioBlob = null;
let currentInterviewId = null;

// DOM要素
const startRecordBtn = document.getElementById('startRecord');
const stopRecordBtn = document.getElementById('stopRecord');
const uploadAudioBtn = document.getElementById('uploadAudio');
const recordingStatus = document.getElementById('recordingStatus');
const recordingTime = document.getElementById('recordingTime');
const audioPreview = document.getElementById('audioPreview');
const audioPlayer = document.getElementById('audioPlayer');
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const fileName = document.getElementById('fileName');
const processingSection = document.getElementById('processingSection');
const processingMessage = document.getElementById('processingMessage');
const progressFill = document.getElementById('progressFill');
const resultSection = document.getElementById('resultSection');
const viewReportBtn = document.getElementById('viewReport');
const interviewList = document.getElementById('interviewList');

// 初期化
document.addEventListener('DOMContentLoaded', () => {
    loadInterviewList();
    setupEventListeners();
});

// イベントリスナー設定
function setupEventListeners() {
    startRecordBtn.addEventListener('click', startRecording);
    stopRecordBtn.addEventListener('click', stopRecording);
    uploadAudioBtn.addEventListener('click', uploadAudio);
    fileInput.addEventListener('change', handleFileSelect);
    viewReportBtn.addEventListener('click', viewReport);
    
    // ドラッグ&ドロップ
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

// 録音開始
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            currentAudioBlob = audioBlob;
            const audioUrl = URL.createObjectURL(audioBlob);
            audioPlayer.src = audioUrl;
            audioPreview.style.display = 'block';
            
            // ボタン状態変更
            uploadAudioBtn.disabled = false;
            startRecordBtn.disabled = false;
            
            // ステータス更新
            recordingStatus.textContent = '録音完了！アップロードボタンを押してください。';
            recordingStatus.className = 'status-message ready';
        };
        
        mediaRecorder.start();
        
        // UI更新
        startRecordBtn.disabled = true;
        stopRecordBtn.disabled = false;
        recordingStatus.textContent = '● 録音中...';
        recordingStatus.className = 'status-message recording';
        
        // タイマー開始
        recordingStartTime = Date.now();
        recordingInterval = setInterval(updateRecordingTime, 100);
        
    } catch (error) {
        console.error('録音開始エラー:', error);
        alert('マイクへのアクセスが拒否されました。ブラウザの設定を確認してください。');
    }
}

// 録音停止
function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        
        stopRecordBtn.disabled = true;
        clearInterval(recordingInterval);
    }
}

// 録音時間更新
function updateRecordingTime() {
    const elapsed = Date.now() - recordingStartTime;
    const minutes = Math.floor(elapsed / 60000);
    const seconds = Math.floor((elapsed % 60000) / 1000);
    recordingTime.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

// ファイル選択処理
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        handleFile(file);
    }
}

// ファイル処理
function handleFile(file) {
    if (!file.type.startsWith('audio/')) {
        alert('音声ファイルを選択してください。');
        return;
    }
    
    currentAudioBlob = file;
    fileName.textContent = `選択: ${file.name}`;
    
    // プレビュー表示
    const audioUrl = URL.createObjectURL(file);
    audioPlayer.src = audioUrl;
    audioPreview.style.display = 'block';
    
    uploadAudioBtn.disabled = false;
}

// 音声アップロード
async function uploadAudio() {
    if (!currentAudioBlob) {
        alert('音声ファイルがありません。');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', currentAudioBlob, 'interview.wav');
    
    try {
        uploadAudioBtn.disabled = true;
        processingSection.style.display = 'block';
        processingMessage.textContent = 'アップロード中...';
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentInterviewId = result.interview_id;
            processingMessage.textContent = '分析中... しばらくお待ちください。';
            startStatusPolling(result.interview_id);
        } else {
            throw new Error('アップロードに失敗しました。');
        }
        
    } catch (error) {
        console.error('アップロードエラー:', error);
        alert('アップロードに失敗しました: ' + error.message);
        uploadAudioBtn.disabled = false;
        processingSection.style.display = 'none';
    }
}

// ステータスポーリング
function startStatusPolling(interviewId) {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${interviewId}`);
            const status = await response.json();
            
            updateProgress(status.status);
            
            if (status.status === 'completed') {
                clearInterval(pollInterval);
                showResult(interviewId);
                loadInterviewList();
            } else if (status.status === 'failed') {
                clearInterval(pollInterval);
                alert('処理に失敗しました: ' + (status.error_message || '不明なエラー'));
                processingSection.style.display = 'none';
            }
            
        } catch (error) {
            console.error('ステータス確認エラー:', error);
        }
    }, 2000); // 2秒ごとにチェック
}

// 進捗更新
function updateProgress(status) {
    const statusMessages = {
        'uploaded': { message: '処理待ち...', progress: 10 },
        'processing': { message: '分析中...', progress: 50 },
        'completed': { message: '完了！', progress: 100 },
        'failed': { message: 'エラー', progress: 0 }
    };
    
    const info = statusMessages[status] || { message: '処理中...', progress: 30 };
    processingMessage.textContent = info.message;
    progressFill.style.width = info.progress + '%';
}

// 結果表示
function showResult(interviewId) {
    processingSection.style.display = 'none';
    resultSection.style.display = 'block';
    
    const resultContent = document.getElementById('resultContent');
    resultContent.innerHTML = `
        <div style="text-align: center; padding: 30px;">
            <div style="font-size: 4em; margin-bottom: 20px;">✅</div>
            <h3>分析が完了しました！</h3>
            <p>詳細なレポートをご確認ください。</p>
        </div>
    `;
    
    viewReportBtn.style.display = 'block';
}

// レポート表示
function viewReport() {
    if (currentInterviewId) {
        window.open(`/api/report/${currentInterviewId}`, '_blank');
    }
}

// 面接一覧読み込み
async function loadInterviewList() {
    try {
        const response = await fetch('/api/interviews');
        const interviews = await response.json();
        
        if (interviews.length === 0) {
            interviewList.innerHTML = '<p style="text-align: center; color: #999;">まだ面接記録がありません。</p>';
            return;
        }
        
        interviewList.innerHTML = interviews.map(interview => {
            const statusClass = `status-${interview.status}`;
            const statusText = {
                'uploaded': 'アップロード済み',
                'processing': '処理中',
                'completed': '完了',
                'failed': '失敗'
            }[interview.status] || interview.status;
            
            const date = new Date(interview.created_at);
            const dateStr = date.toLocaleString('ja-JP');
            
            const viewButton = interview.status === 'completed'
                ? `<button class="btn btn-primary" onclick="window.open('/api/report/${interview.id}', '_blank')">レポート表示</button>`
                : '';
            
            return `
                <div class="interview-item">
                    <div class="interview-info">
                        <h3>${interview.filename}</h3>
                        <p>作成日時: ${dateStr}</p>
                        ${interview.duration ? `<p>長さ: ${Math.floor(interview.duration / 60)}分${Math.floor(interview.duration % 60)}秒</p>` : ''}
                    </div>
                    <div>
                        <span class="interview-status ${statusClass}">${statusText}</span>
                        ${viewButton}
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('面接一覧読み込みエラー:', error);
        interviewList.innerHTML = '<p style="text-align: center; color: #dc3545;">読み込みエラー</p>';
    }
}
