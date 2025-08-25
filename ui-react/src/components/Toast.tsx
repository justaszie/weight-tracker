import type { ToastProps } from "@/types/props";

export default function Toast(props: ToastProps) {
    const categoryToCSSClass = {
        info: "toast__message--info",
        error: "toast__message--error",
        success: "toast__message--success",
    }

    return (
        <div className="toast">
            <p className={`toast__message ${categoryToCSSClass[props.category] || "toast__message--info"}`}>
                {props.message}
            </p>
        </div>
    )
}