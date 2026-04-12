import axios from "axios";
import toast from "react-hot-toast";

const baseURL =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const api = axios.create({
    baseURL,
    timeout: 60000,
    headers: {
        "Content-Type": "application/json",
    },
});

export function setApiAuthToken(token) {
    if (token) {
        api.defaults.headers.common.Authorization = `Bearer ${token}`;
        return;
    }

    delete api.defaults.headers.common.Authorization;
}

api.interceptors.response.use(
    (response) => response,
    (error) => {
        let message = "We could not connect to the server. Please try again.";
        if (error && error.response && error.response.data && error.response.data.error) {
            message = error.response.data.error;
        }
        toast.error(message);
        return Promise.reject(error);
    }
);

export default api;