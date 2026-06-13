import unittest
from unittest.mock import AsyncMock, patch

from submission.app import QueryRequest, handle_type1


PREMISES = [
    "If a researcher completed ethics training and has lab access, then that researcher can handle participant data.",
    "If a researcher can handle participant data and has supervisor approval, then that researcher may join Study Alpha.",
    "Every researcher who may join Study Alpha is listed as an active contributor.",
    "Asha completed ethics training.",
    "Asha has lab access.",
    "Asha has supervisor approval.",
    "Study Alpha has 12 enrolled participants.",
    "No premise states whether Asha has budget approval.",
]


def request(query_id, query, options, premises=None):
    return QueryRequest(
        query_id=query_id,
        type="type1",
        query=query,
        premises=premises or PREMISES,
        options=options,
    )


class Type1QuickCheckTests(unittest.IsolatedAsyncioTestCase):
    async def run_case(self, query_request, raw_response):
        with patch(
            "submission.app.async_call_vllm",
            new=AsyncMock(return_value=raw_response),
        ) as model_call:
            result = await handle_type1(query_request)
            prompt = model_call.await_args.args[0]
        return result, prompt

    async def test_mcq_repairs_unknown_from_supported_option(self):
        result, prompt = await self.run_case(
            request(
                "quick_type1_mc",
                "Based on the premises, which option is logically supported?\n"
                "A. Asha may join Study Alpha\n"
                "B. Asha cannot handle participant data\n"
                "C. Asha has budget approval\n"
                "D. Study Alpha has 20 enrolled participants",
                ["A", "B", "C", "D"],
            ),
            """<think>
**Relevant Premises:** P1, P2, P4, P5, P6
**Reasoning:** Asha can handle participant data and has supervisor approval. Therefore, Asha may join Study Alpha.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "A")
        self.assertEqual(result.premises_used, [0, 1, 3, 4, 5])
        self.assertIn("ALLOWED ANSWERS: A | B | C | D", prompt)

    async def test_yes_no_repairs_answer_from_reasoning(self):
        result, prompt = await self.run_case(
            request(
                "quick_type1_yes_no",
                "Is Asha listed as an active contributor?",
                ["Yes", "No", "Uncertain"],
            ),
            """<think>
**Relevant Premises:** P1, P2, P3, P4, P5, P6
**Reasoning:** Asha may join Study Alpha. Therefore, premise P3 implies that Asha is listed as an active contributor.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "Yes")
        self.assertEqual(result.premises_used, [0, 1, 2, 3, 4, 5])
        self.assertIn("ALLOWED ANSWERS: Yes | No | Uncertain", prompt)

    async def test_uncertain_uses_request_label_and_meta_premise(self):
        result, _ = await self.run_case(
            request(
                "quick_type1_uncertain",
                "Does Asha have budget approval?",
                ["Yes", "No", "Uncertain"],
            ),
            """<think>
**Relevant Premises:**
**Reasoning:** The question cannot be determined because no premise provides information about Asha's budget approval.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "Uncertain")
        self.assertEqual(result.premises_used, [7])

    async def test_number_repairs_unknown_to_concrete_value(self):
        result, prompt = await self.run_case(
            request(
                "quick_type1_number",
                "How many enrolled participants does Study Alpha have?",
                [],
            ),
            """<think>
**Relevant Premises:** P7
**Reasoning:** Premise P7 directly states that Study Alpha has 12 enrolled participants. Therefore the requested number is 12.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "12")
        self.assertEqual(result.premises_used, [6])
        self.assertIn("This is an open-answer question", prompt)

    async def test_text_repairs_unknown_to_entity(self):
        result, _ = await self.run_case(
            request(
                "quick_type1_text",
                "Which researcher may join Study Alpha?",
                [],
            ),
            """<think>
**Relevant Premises:** P1, P2, P4, P5, P6
**Reasoning:** Asha completed ethics training and has lab access, so Asha can handle participant data. Asha also has supervisor approval. Therefore, Asha may join Study Alpha.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "Asha")
        self.assertEqual(result.premises_used, [0, 1, 3, 4, 5])

    async def test_text_answer_is_derived_instead_of_defaulting_to_asha(self):
        premises = [
            "If an analyst passed the audit, then that analyst may join Project Nova.",
            "Bao Tran passed the audit.",
        ]
        result, _ = await self.run_case(
            request(
                "different_entity",
                "Which analyst may join Project Nova?",
                [],
                premises=premises,
            ),
            """<think>
**Relevant Premises:** P1, P2
**Reasoning:** Bao Tran passed the audit. Therefore, Bao Tran may join Project Nova.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "Bao Tran")
        self.assertNotEqual(result.answer, "Asha")
        self.assertEqual(result.premises_used, [0, 1])

    async def test_mcq_is_derived_when_correct_option_is_c(self):
        premises = [
            "Cedar has a security badge.",
            "If Cedar has a security badge, then Cedar may enter Vault Nine.",
            "The cafeteria closes at six.",
        ]
        result, _ = await self.run_case(
            request(
                "anti_hardcode_mcq",
                "Which option is supported?\n"
                "A. Cedar may not enter Vault Nine\n"
                "B. The cafeteria closes at nine\n"
                "C. Cedar may enter Vault Nine\n"
                "D. Cedar lost the security badge",
                ["A", "B", "C", "D"],
                premises=premises,
            ),
            """<think>
**Relevant Premises:** P1, P2
**Reasoning:** Cedar has a security badge. Consequently, Cedar may enter Vault Nine.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "C")
        self.assertEqual(result.premises_used, [0, 1])

    async def test_yes_no_is_derived_when_answer_is_no_and_options_are_reordered(self):
        premises = [
            "No solar-powered drone is approved for night flights.",
            "Kite X is a solar-powered drone.",
        ]
        result, _ = await self.run_case(
            request(
                "anti_hardcode_no",
                "Is Kite X approved for night flights?",
                ["Uncertain", "No", "Yes"],
                premises=premises,
            ),
            """<think>
**Relevant Premises:** P1, P2
**Reasoning:** Kite X is solar-powered. Therefore, Kite X is not approved for night flights.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "No")
        self.assertEqual(result.premises_used, [0, 1])

    async def test_uncertainty_label_and_meta_premise_are_taken_from_request(self):
        premises = [
            "Nia completed orientation.",
            "No record states whether Nia has archive clearance.",
            "The archive opens on Monday.",
        ]
        result, _ = await self.run_case(
            request(
                "anti_hardcode_unknown",
                "Does Nia have archive clearance?",
                ["No", "Unknown", "Yes"],
                premises=premises,
            ),
            """<think>
**Relevant Premises:**
**Reasoning:** There is not enough information to determine whether Nia has archive clearance.
</think>
**Answer:** Uncertain""",
        )

        self.assertEqual(result.answer, "Unknown")
        self.assertEqual(result.premises_used, [1])

    async def test_number_is_extracted_from_changed_value_and_premise_position(self):
        premises = [
            "Room B contains four desks.",
            "Archive Z stores 37 sealed files.",
            "Archive Z is below the library.",
        ]
        result, _ = await self.run_case(
            request(
                "anti_hardcode_number",
                "How many sealed files does Archive Z store?",
                [],
                premises=premises,
            ),
            """<think>
**Relevant Premises:** P2
**Reasoning:** Premise P2 states the file count. Hence, the requested total is 37.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "37")
        self.assertEqual(result.premises_used, [1])

    async def test_text_is_extracted_for_a_different_entity_type(self):
        premises = [
            "If a facility passes inspection, then that facility may host the symposium.",
            "Orion Laboratory passed inspection.",
            "The symposium begins in October.",
        ]
        result, _ = await self.run_case(
            request(
                "anti_hardcode_text",
                "Which facility may host the symposium?",
                [],
                premises=premises,
            ),
            """<think>
**Relevant Premises:** P1, P2
**Reasoning:** Orion Laboratory passed inspection. Consequently, Orion Laboratory may host the symposium.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "Orion Laboratory")
        self.assertEqual(result.premises_used, [0, 1])

    async def test_invalid_mcq_output_does_not_default_to_last_option(self):
        result, _ = await self.run_case(
            request(
                "anti_hardcode_no_positional_fallback",
                "Which option is supported?\nA. One\nB. Two\nC. Three\nD. Four",
                ["A", "B", "C", "D"],
                premises=["No usable conclusion is present."],
            ),
            """<think>
**Relevant Premises:**
**Reasoning:** The response is malformed and supplies no supported option.
</think>
**Answer:** Unknown""",
        )

        self.assertEqual(result.answer, "Unknown")
        self.assertNotEqual(result.answer, "D")


if __name__ == "__main__":
    unittest.main()
