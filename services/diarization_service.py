from nemo.collections.asr.models import SortformerEncLabelModel
from config.settings import MODEL_NAME


class DiarizationService:
    def __init__(self):
        print(f"⏳ NeMo 모델({MODEL_NAME})을 로드하는 중입니다...")
        self.model = SortformerEncLabelModel.from_pretrained(MODEL_NAME)
        self.model.eval()

        # 공식 권장 파라미터 적용
        self.model.sortformer_modules.chunk_len = 340
        self.model.sortformer_modules.chunk_right_context = 40
        self.model.sortformer_modules.fifo_len = 40
        self.model.sortformer_modules.spkcache_update_period = 300
        print("✅ 모델 로드 완료!")

    def process(self, audio_file_path: str) -> list[str]:
        """입력 오디오 파일에 대해 화자 분리 추론을 수행"""
        predicted_segments = self.model.diarize(audio=[audio_file_path], batch_size=1)

        result_list = []
        for segment in predicted_segments[0]:
            result_list.append(str(segment))

        return result_list

    def process_many(self, audio_file_paths: list[str]) -> list[list[str]]:
        """여러 오디오 파일에 대해 배치 화자 분리 추론을 수행"""
        if not audio_file_paths:
            return []
            
        predicted_segments = self.model.diarize(
            audio=audio_file_paths,
            batch_size=len(audio_file_paths)
        )

        all_results = []
        for file_segments in predicted_segments:
            result_list = []
            for segment in file_segments:
                result_list.append(str(segment))
            all_results.append(result_list)

        return all_results


# 서버 시작 시 1번만 메모리에 올라가게 설정
diar_service = DiarizationService()