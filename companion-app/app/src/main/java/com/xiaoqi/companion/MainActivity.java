package com.xiaoqi.companion;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.os.Bundle;
import android.text.InputType;
import android.view.Window;
import android.widget.EditText;
import android.content.SharedPreferences;

public class MainActivity extends Activity {
    private CompanionView companionView;
    private SharedPreferences prefs;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Window w = getWindow();
        w.setStatusBarColor(Color.rgb(246, 241, 234));
        w.setNavigationBarColor(Color.rgb(238, 229, 220));

        prefs = getSharedPreferences("xiaoqi_state", MODE_PRIVATE);
        companionView = new CompanionView(this, prefs);
        setContentView(companionView);
        companionView.beginSession();
    }

    public void openChat() {
        final EditText input = new EditText(this);
        input.setHint("想跟小栖说什么？");
        input.setSingleLine(false);
        input.setMaxLines(4);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);

        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("跟小栖聊聊")
                .setView(input)
                .setPositiveButton("发送", (d, which) -> {
                    String msg = input.getText().toString().trim();
                    if (!msg.isEmpty()) companionView.onUserMessage(msg);
                })
                .setNegativeButton("取消", null)
                .create();
        dialog.show();
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (companionView != null) companionView.persist();
    }
}
