import axios from 'axios'

// 创建 axios 实例
const request = axios.create({
    baseURL: '/api',      // 走 Vite 代理，转发到 FastAPI
    timeout: 60000,        // 60 秒超时（AI 生成慢）
})

// 请求拦截器
request.interceptors.request.use(
    (config) => {
        // 可以在这里加 token 等
        return config
    },
    (error) => Promise.reject(error)
)

// 响应拦截器
request.interceptors.response.use(
    (response) => response.data,
    (error) => {
        console.error('API 请求失败：', error)
        return Promise.reject(error)
    }
)

export default request