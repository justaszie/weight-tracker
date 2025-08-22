type ToastPropsType = {
    category: MessageCategory;
    message: string;
}

type MessageCategory = 'info' | 'error' | 'success'

export default function Toast(props: ToastPropsType) {
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