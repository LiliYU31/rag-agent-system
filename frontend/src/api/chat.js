/**
 * 流式对话（SSE，区分思考与回答）
 * @param {string} query 用户问题
 * @param {string} sessionId 当前会话ID (比如 '2026-10-21')
 * @param {function} onThinking 思考内容的回调
 * @param {function} onAnswer 回答内容的回调
 * @param {function} onDone 完成回调
 * @param {function} onError 错误回调
 */
export async function chatStream(query, sessionId, onThinking, onAnswer, onDone, onError) {
    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // 这里使用传入的 sessionId
            body: JSON.stringify({ query, session_id: sessionId }),
        })

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })
            const parts = buffer.split('\n\n')
            buffer = parts.pop()

            for (const part of parts) {
                if (!part || part.startsWith(':')) continue
                if (!part.startsWith('data: ')) continue

                const content = part.slice(6)
                if (content === '[DONE]') {
                    onDone && onDone()
                    return
                }
                if (content.startsWith('[ERROR]')) {
                    onError && onError(content.slice(8))
                    return
                }

                // 解析 JSON payload
                try {
                    const payload = JSON.parse(content)
                    if (payload.phase === 'thinking') {
                        onThinking && onThinking(payload.content)
                    } else if (payload.phase === 'answer') {
                        onAnswer && onAnswer(payload.content)
                    }
                } catch (e) {
                    console.warn("解析SSE数据失败，跳过此段", content)
                    // 不要直接把错误吞掉，如果它是文本，就直接输出
                    onAnswer && onAnswer(content)
                }
            }
        }

        onDone && onDone()
    } catch (err) {
        onError && onError(err.message)
    }
}

/**
 * 上传文件
 * @param {File} file 文件对象
 * @returns {Promise<Object>} 后端返回的文件信息
 */
export async function uploadFile(file) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
    })

    if (!response.ok) {
        throw new Error(`上传失败：HTTP ${response.status}`)
    }

    return await response.json()
}