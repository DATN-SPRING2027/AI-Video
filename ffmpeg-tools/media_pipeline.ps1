<#
.SYNOPSIS
    FFmpeg Media Pipeline Helper for CreateVideo AI Studio.
    Supports: add-voiceover (Piper TTS), mix-bgm (ACE-Step 1.5), burn-srt / embed-srt (Whisper),
              full-compose (Video + Voiceover + BGM + SRT in 1 step), trim, compress.
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("add-voiceover", "mix-bgm", "burn-srt", "embed-srt", "full-compose", "trim", "compress")]
    [string]$Action,

    [Parameter(Mandatory = $true)]
    [string]$InputVideo,

    [string]$InputVoice = "",
    [string]$InputAudio = "",
    [string]$InputSrt = "",
    [string]$Output = "output.mp4",
    [double]$VoiceVolume = 1.0,
    [double]$BgmVolume = 0.20,
    [string]$Start = "00:00:00",
    [string]$Duration = "00:00:10"
)

$ErrorActionPreference = "Stop"

function Format-FfmpegSubPath([string]$PathStr) {
    $resolved = (Resolve-Path $PathStr).Path
    return ($resolved -replace '\\', '/' -replace ':', '\:' -replace "'", "\'")
}

switch ($Action) {
    "add-voiceover" {
        if (-not $InputVoice) { throw "Missing -InputVoice (WAV/MP3 voiceover from Piper TTS)" }
        ffmpeg -y -i "$InputVideo" -i "$InputVoice" `
            -filter_complex "[1:a]volume=$VoiceVolume[vo]" `
            -map 0:v -map "[vo]" -c:v copy -c:a aac -b:a 192k "$Output"
    }
    "mix-bgm" {
        if (-not $InputAudio) { throw "Missing -InputAudio (BGM file from ACE-Step 1.5)" }
        $hasAudio = ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$InputVideo"
        if ($hasAudio) {
            ffmpeg -y -i "$InputVideo" -stream_loop -1 -i "$InputAudio" `
                -filter_complex "[1:a]volume=$BgmVolume[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]" `
                -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -shortest "$Output"
        } else {
            ffmpeg -y -i "$InputVideo" -stream_loop -1 -i "$InputAudio" `
                -filter_complex "[1:a]volume=$BgmVolume[aout]" `
                -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -shortest "$Output"
        }
    }
    "embed-srt" {
        if (-not $InputSrt) { throw "Missing -InputSrt (.srt file from Whisper)" }
        ffmpeg -y -i "$InputVideo" -i "$InputSrt" -c:v copy -c:a copy -c:s mov_text "$Output"
    }
    "burn-srt" {
        if (-not $InputSrt) { throw "Missing -InputSrt (.srt file from Whisper)" }
        $escapedSrt = Format-FfmpegSubPath $InputSrt
        ffmpeg -y -i "$InputVideo" `
            -vf "subtitles='$escapedSrt':force_style='FontName=Segoe UI,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=28'" `
            -c:v libx264 -crf 18 -preset fast -c:a copy "$Output"
    }
    "full-compose" {
        # Combine Video + optional Voiceover (Piper TTS) + optional BGM (ACE-Step) + optional Burn-in SRT (Whisper)
        $inputs = @("-i", "$InputVideo")
        $idx = 1
        $voIdx = -1
        $bgmIdx = -1

        if ($InputVoice) {
            $inputs += @("-i", "$InputVoice")
            $voIdx = $idx
            $idx++
        }
        if ($InputAudio) {
            $inputs += @("-stream_loop", "-1", "-i", "$InputAudio")
            $bgmIdx = $idx
            $idx++
        }

        $vfArgs = @()
        $vCodec = @("-c:v", "copy")
        if ($InputSrt) {
            $escapedSrt = Format-FfmpegSubPath $InputSrt
            $vfArgs = @("-vf", "subtitles='$escapedSrt':force_style='FontName=Segoe UI,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=28'")
            $vCodec = @("-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p")
        }

        if ($voIdx -ge 0 -and $bgmIdx -ge 0) {
            $fc = "[$voIdx`:a]volume=$VoiceVolume[vo];[$bgmIdx`:a]volume=$BgmVolume[bgm];[vo][bgm]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[aout]"
            & ffmpeg -y @inputs -filter_complex $fc @vfArgs -map 0:v -map "[aout]" @vCodec -c:a aac -b:a 192k -movflags +faststart "$Output"
        } elseif ($voIdx -ge 0) {
            $fc = "[$voIdx`:a]volume=$VoiceVolume[aout]"
            & ffmpeg -y @inputs -filter_complex $fc @vfArgs -map 0:v -map "[aout]" @vCodec -c:a aac -b:a 192k -movflags +faststart "$Output"
        } elseif ($bgmIdx -ge 0) {
            $fc = "[$bgmIdx`:a]volume=$BgmVolume[aout]"
            & ffmpeg -y @inputs -filter_complex $fc @vfArgs -map 0:v -map "[aout]" @vCodec -c:a aac -b:a 192k -shortest -movflags +faststart "$Output"
        } else {
            & ffmpeg -y @inputs @vfArgs @vCodec -c:a copy -movflags +faststart "$Output"
        }
    }
    "trim" {
        ffmpeg -y -ss "$Start" -i "$InputVideo" -t "$Duration" -c:v libx264 -crf 18 -c:a aac "$Output"
    }
    "compress" {
        ffmpeg -y -i "$InputVideo" -c:v libx264 -crf 23 -preset medium -c:a aac -b:a 128k -movflags +faststart "$Output"
    }
}

Write-Host "[FFmpeg Pipeline] Completed video export: $Output" -ForegroundColor Green
