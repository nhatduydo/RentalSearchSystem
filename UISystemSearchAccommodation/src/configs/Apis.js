import axios from "axios";

const BASE_URL = 'https://9313-2402-800-6315-33d1-adab-32ce-26a-45bb.ngrok-free.app/'

export const endpoints = {
    'users': '/user/',
    'landlords': '/landlords/',
    'tenants': '/tenants/',
    'motels': '/motels/',
    'rooms': '/rooms/',
    'posts': '/posts/',
    'comments': '/comments/',
    'motelRatings': '/motelRatings/',
    'payments': '/payments/',
    'payments-checkout': '/payments/checkout/',
    'searchs': '/searchs/',
    'search-historys': '/search-historys/',
    'chat-rooms': '/chat-rooms/',
    'follows': '/follows/',
    'room-tenants': '/room-tenants/'
}

export default axios.create({
    baseURL: BASE_URL
});