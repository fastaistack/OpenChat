
from typing import Any, Dict, List, Optional
from langchain_text_splitters import RecursiveJsonSplitter


class CustomRecursiveJsonSplitter(RecursiveJsonSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _json_split(
        self,
        data: Dict[str, Any],
        current_path: Optional[List[str]] = None,
        chunks: Optional[List[Dict]] = None,
    ) -> List[Dict]:
        """
        Split json into maximum size dictionaries while preserving structure.
        """
        current_path = current_path or []
        chunks = chunks or [{}]

        if isinstance(data, dict):
            for key, value in data.items():
                new_path = current_path + [key]
                chunk_size = self._json_size(chunks[-1])
                size = self._json_size({key: value})
                remaining = self.max_chunk_size - chunk_size

                if size < remaining:
                    # Add item to current chunk
                    self._set_nested_dict(chunks[-1], new_path, value)
                else:
                    if chunk_size >= self.min_chunk_size:
                        # Chunk is big enough, start a new chunk
                        chunks.append({})

                    # Iterate
                    self._json_split(value, new_path, chunks)
        else:
            # handle single item
            self._set_nested_dict(chunks[-1], current_path, data)
        return chunks
