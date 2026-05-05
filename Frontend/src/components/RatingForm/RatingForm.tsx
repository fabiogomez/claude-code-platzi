"use client";

import { FC, useState } from "react";
import { getUserId } from "@/utils/userId";
import styles from "./RatingForm.module.scss";

interface RatingFormProps {
  courseSlug: string;
  onRatingSubmitted?: () => void;
}

export const RatingForm: FC<RatingFormProps> = ({ courseSlug, onRatingSubmitted }) => {
  const [hoveredStar, setHoveredStar] = useState<number>(0);
  const [selectedScore, setSelectedScore] = useState<number>(0);
  const [comment, setComment] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitMessage, setSubmitMessage] = useState<string>("");
  const [submitError, setSubmitError] = useState<boolean>(false);

  const handleSubmit = async () => {
    if (selectedScore === 0) return;

    setIsSubmitting(true);
    setSubmitMessage("");
    setSubmitError(false);

    const userId = getUserId();

    try {
      const body: { score: number; user_identifier: string; comment?: string } = {
        score: selectedScore,
        user_identifier: userId,
      };

      if (comment.trim()) {
        body.comment = comment.trim();
      }

      const res = await fetch(`http://localhost:8000/courses/${courseSlug}/ratings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error("Failed to submit rating");
      }

      setSubmitMessage("Rating submitted successfully");
      setSubmitError(false);
      setSelectedScore(0);
      setComment("");
      onRatingSubmitted?.();
    } catch {
      setSubmitMessage("Error submitting rating. Please try again.");
      setSubmitError(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Rate this course</h3>

      <div className={styles.starsContainer}>
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            className={`${styles.starButton} ${
              star <= (hoveredStar || selectedScore) ? styles.starActive : ""
            }`}
            onMouseEnter={() => setHoveredStar(star)}
            onMouseLeave={() => setHoveredStar(0)}
            onClick={() => setSelectedScore(star)}
            aria-label={`Rate ${star} out of 5 stars`}
          >
            &#9733;
          </button>
        ))}
        {selectedScore > 0 && (
          <span className={styles.scoreIndicator}>{selectedScore}/5</span>
        )}
      </div>

      <textarea
        className={styles.commentInput}
        placeholder="Leave an optional comment..."
        value={comment}
        onChange={(e) => setComment(e.target.value)}
        maxLength={1000}
        rows={3}
      />

      <button
        type="button"
        className={styles.submitButton}
        onClick={handleSubmit}
        disabled={selectedScore === 0 || isSubmitting}
      >
        {isSubmitting ? "Submitting..." : "Submit Rating"}
      </button>

      {submitMessage && (
        <p className={submitError ? styles.errorMessage : styles.successMessage}>
          {submitMessage}
        </p>
      )}
    </div>
  );
};
