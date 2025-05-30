import axios from "axios";

const BASE_URL = 'https://systemaccommodation.online';

const instance = axios.create({
    baseURL: BASE_URL,
});

export const endpoints = {
    'oauth2-token': '/oauth/token/',
    'users': '/users/',
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
    'room-tenants': '/room-tenants/',
    'room-images': '/room-images/',
    'motel-images': '/motel-images/',
    'notifications': '/notifications/',
};

export default instance;
