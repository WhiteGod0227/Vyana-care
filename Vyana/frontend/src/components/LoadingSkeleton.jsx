function LoadingSkeleton({ height = 80, radius = 16, style = {} }) {
  return (
    <div
      className="vy-skeleton"
      style={{
        height,
        borderRadius: radius,
        ...style,
      }}
    />
  );
}

export default LoadingSkeleton;
