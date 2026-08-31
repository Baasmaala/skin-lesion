import "./Button.css";

/**
 * Reusable button.
 * variant: "primary" | "secondary" | "outline"
 * as: renders a <Link>-like element when `to` is passed via props.as, otherwise a <button>
 */
export default function Button({
  children,
  variant = "primary",
  size = "md",
  icon = null,
  as: As = "button",
  className = "",
  ...props
}) {
  return (
    <As className={`btn btn--${variant} btn--${size} ${className}`} {...props}>
      {children}
      {icon && <span className="btn__icon">{icon}</span>}
    </As>
  );
}
