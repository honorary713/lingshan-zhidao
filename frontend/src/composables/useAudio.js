/**
 * 音频工具 composable — 语音录制、WAV 转换、TTS 播放
 */
import { ref } from 'vue'

export function useAudio() {
  const isRecording = ref(false)
  let mediaRecorder = null
  let audioChunks = []
  let currentAudioEl = null
  let currentAudioNodes = null
  let sharedAudioCtx = null
  let mouthRaf = null

  // ===== WAV 转换 =====
  async function convertToWav(blob) {
    const arrayBuffer = await blob.arrayBuffer()
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)()
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer)
    const numChannels = audioBuffer.numberOfChannels
    const sampleRate = 16000
    const length = Math.floor(audioBuffer.length * sampleRate / audioBuffer.sampleRate)
    const offlineCtx = new OfflineAudioContext(numChannels, length, sampleRate)
    const source = offlineCtx.createBufferSource()
    source.buffer = audioBuffer
    source.connect(offlineCtx.destination)
    source.start(0)
    const resampled = await offlineCtx.startRendering()
    const wavData = _buildWav(resampled)
    audioCtx.close()
    return new Blob([wavData], { type: 'audio/wav' })
  }

  function _buildWav(audioBuffer) {
    const numChannels = audioBuffer.numberOfChannels
    const sampleRate = audioBuffer.sampleRate
    const bitDepth = 16
    const bytesPerSample = bitDepth / 8
    const blockAlign = numChannels * bytesPerSample
    const dataLength = audioBuffer.length * blockAlign
    const buffer = new ArrayBuffer(44 + dataLength)
    const view = new DataView(buffer)
    _writeStr(view, 0, 'RIFF')
    view.setUint32(4, 36 + dataLength, true)
    _writeStr(view, 8, 'WAVE')
    _writeStr(view, 12, 'fmt ')
    view.setUint32(16, 16, true)
    view.setUint16(20, 1, true)
    view.setUint16(22, numChannels, true)
    view.setUint32(24, sampleRate, true)
    view.setUint32(28, sampleRate * blockAlign, true)
    view.setUint16(32, blockAlign, true)
    view.setUint16(34, bitDepth, true)
    _writeStr(view, 36, 'data')
    view.setUint32(40, dataLength, true)
    let offset = 44
    for (let i = 0; i < audioBuffer.length; i++) {
      for (let ch = 0; ch < numChannels; ch++) {
        const s = Math.max(-1, Math.min(1, audioBuffer.getChannelData(ch)[i]))
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
        offset += bytesPerSample
      }
    }
    return buffer
  }

  function _writeStr(view, offset, str) {
    for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i))
  }

  // ===== 录音 =====
  function startRecording() {
    return new Promise((resolve, reject) => {
      if (!navigator.mediaDevices?.getUserMedia) {
        reject(new Error('浏览器不支持录音功能'))
        return
      }
      isRecording.value = true
      audioChunks = []
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
          if (!isRecording.value) { stream.getTracks().forEach(t => t.stop()); resolve(null); return }
          mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })
          mediaRecorder.ondataavailable = e => { if (e.data.size > 0) audioChunks.push(e.data) }
          mediaRecorder.onstop = async () => {
            stream.getTracks().forEach(t => t.stop())
            if (audioChunks.length > 0) {
              const blob = new Blob(audioChunks, { type: 'audio/webm' })
              const wavBlob = await convertToWav(blob)
              resolve(wavBlob)
            } else {
              resolve(null)
            }
          }
          mediaRecorder.start(100)
        })
        .catch(err => { isRecording.value = false; reject(err) })
    })
  }

  function stopRecording() {
    if (!isRecording.value || !mediaRecorder) return
    if (mediaRecorder.state === 'recording') mediaRecorder.stop()
  }

  // ===== AudioContext 管理 =====
  function getAudioContext() {
    if (!sharedAudioCtx || sharedAudioCtx.state === 'closed') {
      sharedAudioCtx = new (window.AudioContext || window.webkitAudioContext)()
    }
    if (sharedAudioCtx.state === 'suspended') sharedAudioCtx.resume()
    return sharedAudioCtx
  }

  // ===== 音频播放 + 口型驱动 =====
  function playAudioWithLipSync(audioBase64, live2dRef) {
    return new Promise(resolve => {
      if (!live2dRef?.value || !audioBase64) { resolve(); return }
      stopAllAudio(live2dRef)
      const audio = new Audio()
      currentAudioEl = audio
      audio.crossOrigin = 'anonymous'
      audio.src = audioBase64.startsWith('data:')
        ? audioBase64
        : `data:audio/mp3;base64,${audioBase64}`
      const ctx = getAudioContext()
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 256
      const source = ctx.createMediaElementSource(audio)
      source.connect(analyser)
      analyser.connect(ctx.destination)
      currentAudioNodes = { source, analyser }
      const dataArray = new Uint8Array(analyser.frequencyBinCount)

      function onEnd() {
        live2dRef.value?.setMouth(0)
        live2dRef.value?.stopTalking()
        try { source.disconnect() } catch (e) { /* ignore */ }
        try { analyser.disconnect() } catch (e) { /* ignore */ }
        currentAudioEl = null
        currentAudioNodes = null
        mouthRaf = null
        resolve()
      }

      let tickCounter = 0
      function updateMouth() {
        if (audio.paused || audio.ended) { onEnd(); return }
        analyser.getByteFrequencyData(dataArray)
        const avg = dataArray.reduce((a, b) => a + b, 0) / dataArray.length
        live2dRef.value?.setMouth(Math.min(1, avg / 128))
        // 驱动说话期间的身体动作，每秒约 60 帧
        tickCounter++
        live2dRef.value?.onTalkingTick(tickCounter)
        mouthRaf = requestAnimationFrame(updateMouth)
      }

      audio.addEventListener('canplaythrough', () => {
        audio.play().then(() => updateMouth()).catch(() => resolve())
      }, { once: true })
      audio.addEventListener('error', () => resolve(), { once: true })
      audio.load()
    })
  }

  function stopAllAudio(live2dRef) {
    if (currentAudioEl) {
      try { currentAudioEl.pause() } catch (e) { /* ignore */ }
      try { currentAudioEl.src = '' } catch (e) { /* ignore */ }
      currentAudioEl = null
    }
    if (currentAudioNodes) {
      try { currentAudioNodes.source.disconnect() } catch (e) { /* ignore */ }
      try { currentAudioNodes.analyser.disconnect() } catch (e) { /* ignore */ }
      currentAudioNodes = null
    }
    if (mouthRaf) { cancelAnimationFrame(mouthRaf); mouthRaf = null }
    if (typeof speechSynthesis !== 'undefined') { speechSynthesis.cancel() }
    if (live2dRef?.value) {
      live2dRef.value.setMouth(0)
      live2dRef.value.stopTalking()
    }
  }

  function cleanup() {
    stopAllAudio({ value: null })
    if (sharedAudioCtx && sharedAudioCtx.state !== 'closed') {
      sharedAudioCtx.close().catch(() => {})
      sharedAudioCtx = null
    }
    if (mediaRecorder && mediaRecorder.state === 'recording') mediaRecorder.stop()
  }

  return {
    isRecording,
    startRecording,
    stopRecording,
    playAudioWithLipSync,
    stopAllAudio,
    cleanup,
    getAudioContext
  }
}
