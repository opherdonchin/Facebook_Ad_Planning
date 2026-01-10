# Regex: \\\.  matches a backslash followed by a literal dot
# Regex: .* is the wildcard (match anything)
$skipPatterns = '(\\\.|node_modules|bin|obj|debug|release)'

Get-ChildItem -Recurse | 
    Where-Object { $_.FullName -notmatch $skipPatterns } | 
    ForEach-Object {
        $depth = ($_.FullName.Replace($PWD.Path, "").Split([System.IO.Path]::DirectorySeparatorChar).Count - 1)
        "  " * $depth + $_.Name
    } > dirlist.txt