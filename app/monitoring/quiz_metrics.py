from dataclasses import dataclass, field
import time


@dataclass
class QuizMetrics:
    """
    Tracks quiz generation pipeline performance,
    quality, validation, cache, and hardware-related timing.
    """

    topic: str = ""

    # ==========================
    # Timer
    # ==========================

    start_time: float = field(
        default_factory=time.perf_counter
    )


    # ==========================
    # Pipeline Metrics
    # ==========================

    notes_loaded: int = 0

    facts_extracted: int = 0

    facts_used: int = 0



    # ==========================
    # Question Metrics
    # ==========================

    questions_requested: int = 0

    questions_generated: int = 0

    questions_accepted: int = 0

    questions_rejected: int = 0



    # ==========================
    # Validation Metrics
    # ==========================

    validation_failures: dict = field(
        default_factory=dict
    )



    # ==========================
    # LLM Performance Metrics
    # ==========================

    llm_calls: int = 0

    llm_time: float = 0.0



    # ==========================
    # Hardware Performance Metrics
    # ==========================

    cpu_samples: list = field(
        default_factory=list
    )

    ram_samples: list = field(
        default_factory=list
    )

    gpu_samples: list = field(
        default_factory=list
    )



    # ==========================
    # Cache Metrics
    # ==========================

    cache_hit: bool = False

    fallback_used: bool = False



    # ==========================
    # Methods
    # ==========================


    def add_failure(self, category: str):
        """
        Record validation failure.
        """

        self.validation_failures[category] = (
            self.validation_failures.get(category, 0) + 1
        )



    def record_llm_call(self, duration: float):
        """
        Record one LLM generation call.
        """

        self.llm_calls += 1

        self.llm_time += duration



    def record_cpu(self, usage: float):
        """
        Record CPU percentage sample.
        """

        self.cpu_samples.append(
            round(usage, 2)
        )



    def record_ram(self, usage: float):
        """
        Record RAM percentage sample.
        """

        self.ram_samples.append(
            round(usage, 2)
        )



    def record_gpu(self, usage: float):
        """
        Record GPU usage sample.
        """

        self.gpu_samples.append(
            round(usage, 2)
        )



    def generation_time(self):

        return round(
            time.perf_counter() - self.start_time,
            4
        )



    def average(self, values):

        if not values:
            return 0

        return round(
            sum(values) / len(values),
            2
        )



    def report(self):

        return {

            "topic":
                self.topic,


            # ==========================
            # Timing
            # ==========================

            "generation_time":
                self.generation_time(),


            "llm_calls":
                self.llm_calls,


            "llm_time":
                round(
                    self.llm_time,
                    4
                ),



            # ==========================
            # Pipeline
            # ==========================

            "notes_loaded":
                self.notes_loaded,


            "facts_extracted":
                self.facts_extracted,


            "facts_used":
                self.facts_used,



            # ==========================
            # Questions
            # ==========================

            "questions_requested":
                self.questions_requested,


            "questions_generated":
                self.questions_generated,


            "questions_accepted":
                self.questions_accepted,


            "questions_rejected":
                self.questions_rejected,



            # ==========================
            # Validation
            # ==========================

            "validation_failures":
                self.validation_failures,



            # ==========================
            # Hardware
            # ==========================

            "average_cpu":
                self.average(
                    self.cpu_samples
                ),


            "average_ram":
                self.average(
                    self.ram_samples
                ),


            "average_gpu":
                self.average(
                    self.gpu_samples
                ),



            # ==========================
            # Cache
            # ==========================

            "cache_hit":
                self.cache_hit,


            "fallback_used":
                self.fallback_used,

        }