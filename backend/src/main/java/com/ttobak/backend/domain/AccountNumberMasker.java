package com.ttobak.backend.domain;

/**
 * 계좌번호 마스킹. 마지막 그룹을 "****" + 끝 2자리로 바꾼다.
 * 9876-54-321098 → 9876-54-****98, 3333-01-1234567 → 3333-01-****67 (examples/counterparties.json 기준)
 */
public final class AccountNumberMasker {

    private AccountNumberMasker() {
    }

    public static String mask(String accountNumber) {
        if (accountNumber == null || accountNumber.isBlank()) {
            return null;
        }
        String s = accountNumber.trim();
        int dash = s.lastIndexOf('-');
        String head = dash >= 0 ? s.substring(0, dash + 1) : "";
        String last = dash >= 0 ? s.substring(dash + 1) : s;
        String tail = last.length() >= 2 ? last.substring(last.length() - 2) : last;
        return head + "****" + tail;
    }
}
