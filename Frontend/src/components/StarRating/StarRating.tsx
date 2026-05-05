import { FC } from "react";
import styles from "./StarRating.module.scss";

interface StarRatingProps {
  average: number;
  count: number;
  size?: "sm" | "md";
}

export const StarRating: FC<StarRatingProps> = ({ average, count, size = "md" }) => {
  const fullStars = Math.floor(average);
  const hasHalfStar = average - fullStars >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

  const infoText = average === 0 && count === 0
    ? "No ratings (0)"
    : `${average.toFixed(1)} (${count})`;

  return (
    <div className={`${styles.container} ${styles[size]}`}>
      <span className={styles.stars} aria-label={`Rating: ${average.toFixed(1)} out of 5`}>
        {Array.from({ length: fullStars }, (_, i) => (
          <span key={`full-${i}`} className={styles.starFull}>&#9733;</span>
        ))}
        {hasHalfStar && (
          <span className={styles.starHalf}>&#9733;</span>
        )}
        {Array.from({ length: emptyStars }, (_, i) => (
          <span key={`empty-${i}`} className={styles.starEmpty}>&#9734;</span>
        ))}
      </span>
      <span className={styles.info}>{infoText}</span>
    </div>
  );
};
