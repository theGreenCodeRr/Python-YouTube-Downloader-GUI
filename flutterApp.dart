import 'package:flutter/material.dart';
import 'package.http/http.dart' as http;
import 'dart:convert';
import 'package:url_launcher/url_launcher.dart';

// --- IMPORTANT ---
// You must update this URL to point to your server's IP address.
// 'localhost' or '127.0.0.1' will NOT work from a mobile device.
// Use your computer's local network IP (e.g., 'http://192.168.1.10:5000')
const String serverUrl = 'http://127.0.0.1:5000';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  // Theme state
  ThemeMode _themeMode = ThemeMode.dark;

  void toggleTheme() {
    setState(() {
      _themeMode = _themeMode == ThemeMode.light
          ? ThemeMode.dark
          : ThemeMode.light;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Video Downloader',
      theme: ThemeData.light(),
      darkTheme: ThemeData.dark(),
      themeMode: _themeMode,
      home: HomePage(onToggleTheme: toggleTheme),
      debugShowCheckedModeBanner: false,
    );
  }
}

class HomePage extends StatefulWidget {
  final VoidCallback onToggleTheme;
  const HomePage({Key? key, required this.onToggleTheme}) : super(key: key);

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _urlController = TextEditingController();

  // State variables
  String _videoTitle = '';
  List<VideoFormat> _formats = [];
  VideoFormat? _selectedFormat;
  bool _isLoading = false;
  String _status = 'Paste a URL to begin';
  String _currentUrl = '';

  // API call to fetch formats
  Future<void> _fetchFormats() async {
    final url = _urlController.text;
    if (url.isEmpty) {
      setState(() => _status = 'Please paste a URL first.');
      return;
    }

    setState(() {
      _isLoading = true;
      _status = 'Fetching formats...';
      _formats = [];
      _selectedFormat = null;
      _videoTitle = '';
      _currentUrl = url;
    });

    try {
      final response = await http.post(
        Uri.parse('$serverUrl/api/fetch_formats'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'url': url}),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        final List<VideoFormat> formats = (data['formats'] as List)
            .map((f) => VideoFormat.fromJson(f))
            .toList();

        setState(() {
          _videoTitle = data['title'] ?? 'Unknown Title';
          _formats = formats;
          _status = 'Select a format to download.';
        });
      } else {
        final data = json.decode(response.body);
        throw ErrorDescription(data['error'] ?? 'Failed to fetch formats');
      }
    } catch (e) {
      setState(() => _status = 'Error: ${e.toString()}');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  // Triggers the download by launching a URL
  Future<void> _downloadVideo() async {
    if (_selectedFormat == null) {
      setState(() => _status = 'Please select a format first.');
      return;
    }

    // Build the final download URL
    final downloadUrl = Uri.parse(
      '$serverUrl/download?url=$_currentUrl&format_id=${_selectedFormat!.id}&title=$_videoTitle',
    );

    setState(() {
      _status = 'Starting download...';
    });

    // Use url_launcher to open the URL.
    // The browser will handle the file download.
    if (await canLaunchUrl(downloadUrl)) {
      await launchUrl(downloadUrl);
      setState(() => _status = 'Download started in browser.');
    } else {
      setState(() => _status = 'Error: Could not launch URL.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Video Downloader'),
        actions: [
          IconButton(
            icon: Icon(
              Theme.of(context).brightness == Brightness.dark
                  ? Icons.light_mode
                  : Icons.dark_mode,
            ),
            onPressed: widget.onToggleTheme,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // --- URL Input ---
            TextField(
              controller: _urlController,
              decoration: const InputDecoration(
                labelText: 'Paste Video URL',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 12),
            ElevatedButton(
              onPressed: _isLoading ? null : _fetchFormats,
              child: const Text('Fetch Formats'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
            const SizedBox(height: 20),

            // --- Status & Loader ---
            if (_isLoading)
              const Center(child: CircularProgressIndicator())
            else
              Center(
                child: Text(
                  _status,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            const SizedBox(height: 10),

            // --- Video Title ---
            if (_videoTitle.isNotEmpty)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 8.0),
                child: Text(
                  _videoTitle,
                  style: Theme.of(context).textTheme.titleMedium,
                  textAlign: TextAlign.center,
                ),
              ),

            // --- Format List ---
            if (_formats.isNotEmpty)
              Container(
                height: 300,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade600),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: ListView.builder(
                  itemCount: _formats.length,
                  itemBuilder: (context, index) {
                    final format = _formats[index];
                    final isSelected = _selectedFormat == format;

                    return ListTile(
                      title: Text(
                        '${format.res} (${format.ext}) - ${format.size}',
                      ),
                      subtitle: Text(
                        format.note,
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                      tileColor: isSelected
                          ? Theme.of(
                              context,
                            ).colorScheme.primary.withOpacity(0.2)
                          : null,
                      onTap: () {
                        setState(() {
                          _selectedFormat = format;
                        });
                      },
                    );
                  },
                ),
              ),
            const SizedBox(height: 12),

            // --- Download Button ---
            ElevatedButton(
              onPressed: _selectedFormat == null || _isLoading
                  ? null
                  : _downloadVideo,
              child: const Text('Download Selected'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 12),
                backgroundColor: Theme.of(context).colorScheme.primary,
                foregroundColor: Theme.of(context).colorScheme.onPrimary,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// --- Data Model for a Format ---
class VideoFormat {
  final String id;
  final String ext;
  final String res;
  final String note;
  final String size;

  VideoFormat({
    required this.id,
    required this.ext,
    required this.res,
    required this.note,
    required this.size,
  });

  factory VideoFormat.fromJson(Map<String, dynamic> json) {
    return VideoFormat(
      id: json['id'] ?? '',
      ext: json['ext'] ?? '?',
      res: json['res'] ?? '?',
      note: json['note'] ?? '',
      size: json['size_str'] ?? '?',
    );
  }
}
