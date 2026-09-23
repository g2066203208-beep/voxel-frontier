extends Node2D

# IMPORTANT: this controller never changes the source keyframes.
# It only selects clips that already exist in the official Godot Skeleton2D demo.
const CLIPS := ["idle", "walk", "run", "fly", "fall", "jump", "land", "land_hard"]
var clip_index := 0
var elapsed := 0.0
var hold_time := 2.0

@onready var player := $Player
@onready var animation_player: AnimationPlayer = $Player/AnimationPlayer
@onready var animation_tree: AnimationTree = $Player/AnimationTree
@onready var label: Label = $UI/Panel/VBox/ClipLabel

func _ready() -> void:
    player.set_physics_process(false)
    animation_tree.active = false
    if player.has_node("Camera2D"):
        player.get_node("Camera2D").enabled = false
    _build_buttons()
    _play_clip(0)

func _process(delta: float) -> void:
    elapsed += delta
    if elapsed >= hold_time:
        _play_clip((clip_index + 1) % CLIPS.size())

func _build_buttons() -> void:
    var row := $UI/Panel/VBox/Buttons
    for i in CLIPS.size():
        var b := Button.new()
        b.text = CLIPS[i]
        b.pressed.connect(func(index := i): _play_clip(index))
        row.add_child(b)

func _play_clip(index: int) -> void:
    clip_index = index
    elapsed = 0.0
    var clip := CLIPS[clip_index]
    animation_player.stop()
    animation_player.play(clip)
    var a := animation_player.get_animation(clip)
    hold_time = max(1.2, min(2.6, a.length if a != null else 2.0))
    label.text = "Godot 官方 Skeleton2D · 原始动画: %s" % clip
