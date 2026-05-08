from state import State, CameraState, VoiceState  # dataclassをインポート

print("a")

try:
    print("a")

    # 1. 現在の情報を取得（仮の文字列を入れています）
    # 実際にはここで camera.get_info() などの戻り値を入れます
    current_camera = CameraState(c_inf="前方に障害物あり")
    current_voice = VoiceState(v_inf=None)
    input_state = State(voice=current_voice, camera=current_camera)
    print("a")
    print(input_state)

except Exception as e:
    print(e)
