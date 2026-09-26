import 'package:flutter/material.dart';
import 'package:frontend/objects.dart';

class AttachmentCard extends StatelessWidget {
  final AttachmentBase file;
  final VoidCallback? onRemove;
  final bool viewOnly;

  const AttachmentCard({
    super.key,
    required this.file,
    required this.onRemove,
    this.viewOnly = false,
  });

  dynamic _selectIcon(String exp) {
    switch (exp) {
      // Image cases
      case "png":
      case "jpg":
      case "jpeg":
        return file.data != null
            ? Image.memory(file.data!, fit: BoxFit.contain)
            : Icons.image;

      // Image cases (no visualization)
      case "webp":
      case "svg":
      case "gif":
        return Icons.image;

      // Video cases
      case "mp4":
      case "mkv":
        return Icons.video_file;

      // Audio file
      case "mp3":
      case "wav":
        return Icons.audio_file;

      default:
        return Icons.text_snippet;
    }
  }

  @override
  Widget build(BuildContext context) {
    final image = _selectIcon(file.name.split('.').last.toLowerCase());

    return Card(
      child: SizedBox(
        width: 180,
        child: (viewOnly && image is Widget)
            ? image
            : Row(
                children: [
                  SizedBox(
                    width: 56,
                    height: 56,
                    child: image is Widget ? image : Icon(image),
                  ),

                  SizedBox(width: 8),

                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(file.name, overflow: TextOverflow.ellipsis),

                        Text("${(file.size / 1024).toStringAsFixed(1)} KB"),
                      ],
                    ),
                  ),

                  if (onRemove != null)
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: onRemove,
                    ),
                ],
              ),
      ),
    );
  }
}
