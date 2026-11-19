-- The members someone follows are listed like their followers, the most recent first.

CREATE INDEX idx_follows_follower ON FOLLOWS (follower_id, created_at);
