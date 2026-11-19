-- Lists show published articles newest first and continue from the date and id
-- of the last one shown.

CREATE INDEX idx_articles_lists ON ARTICLES (status, publish_date, article_id);
