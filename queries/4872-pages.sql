-- Root pages that hit DOMClobberedShadowedDocumentPropertyAccessed (4872): a named property on
-- `document` was returned while the prototype chain also has that name. The rows with
-- page = '(total)' give the number of root pages per client.
WITH p AS (
  SELECT
    client,
    page,
    rank,
    EXISTS(SELECT 1 FROM UNNEST(features) WHERE id = '4872' AND type = 'default') AS hit
  FROM `httparchive.crawl.pages`
  WHERE date = '2026-10-01'
    AND is_root_page
)
SELECT client, page, rank FROM p WHERE hit
UNION ALL
SELECT client, '(total)', COUNT(*) FROM p GROUP BY client
ORDER BY client, rank
