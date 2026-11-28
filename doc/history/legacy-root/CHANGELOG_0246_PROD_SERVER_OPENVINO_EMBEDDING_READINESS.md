# Changelog 0246 - OpenVINO embedding readiness

## r1

Added explicit OpenVINO embedding readiness for the production server path.

The patch locks the multilingual-e5-small shape used before Qdrant projection:
384 dimensions, normalized vectors, mean pooling, cosine distance, and E5 query
and passage prefixes.
