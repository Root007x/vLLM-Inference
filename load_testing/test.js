import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
    vus: 100,           
    duration: "30s",  
};

export default function () {
    const res = http.post(
        "http://localhost:9000/v1/chat/stream",
        JSON.stringify({
            messages: [{ role: "user", content: "write about human and animal" }],
            max_tokens: 512,
            temperature: 0.7,
        }),
        {
            headers: {
                "Content-Type": "application/json",
                "x-api-key": "my_secret_api_key",
            },
        }
    );

    check(res, {
        "is status 200": (r) => r.status === 200,
    });

    sleep(5);
}