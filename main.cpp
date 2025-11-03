#include <bits/stdc++.h>
#include <fstream>
using namespace std;

void print(vector<int> match, string& T){
    for(int pos : match){
        for(int i = pos; i < pos+50; i++){
            cout << T[i];
        }
        cout << endl;
        return;
    }
}

string toLowerCase(const string &s){
    string result;
    for(char c : s){
        result += tolower(c);
    }
    return result;
}

string cleanWord(const string &s){
    string result;
    for(char c : s){
        if(isalpha(c)){
            result += c;
        }
    }
    return result;
}

vector<int> lps(string P){
    int m = P.size();
    vector<int> v(m, 0);

    int j = 0;
    int i = 1;

    while(i < m){
        if(P[i] == P[j]){
            v[i] = j + 1;
            i++;
            j++;
        }
        else{
            if(j == 0){
                v[i] = 0;
                i++;
            }
            else{
                j = v[j - 1];
            }
        }
    }
    return v;
}

vector<int> kmp(string P, const string& T){
    int n = T.size();
    int m = P.size();
    vector<int> v =lps(P);
    vector<int> match;
    int i = 0;
    int j = 0;
    while(i < n){
        if(T[i] == P[j]){
            i++;
            j++;
        }
        if(j == m){
            match.push_back(i-j);
            j = v[j-1];
        }
        else if (T[i] != P[j]){
            if(j == 0){
                i++;
            }
            else{
                j = v[j-1];
            }
        }
    }
    return match;
}

int main(){
    string filename;
    cout << "Enter filename: ";
    cin >> filename;
    cout << endl;
    ifstream file(filename);
    if(!file.is_open()){
        cerr << "Error opening file" << endl;
        return 1;
    }
    stringstream buffer;
    buffer << file.rdbuf();
    string text = buffer.str();
    set<string> uniqueWords;
    string line;

    while(getline(file, line)){
        stringstream ss(line);
        string rawWord;

        while(ss >> rawWord){
            string word = cleanWord(rawWord);
            word = toLowerCase(word);

            if(!word.empty()){
                uniqueWords.insert(word);
            }
        }
    }
    file.close();

    cout << "Word to search: ";
    string pattern;
    cin >> pattern;
    auto start = chrono::high_resolution_clock::now();
    auto match = kmp(pattern, text);
    auto end = chrono::high_resolution_clock::now();
    auto dur = chrono::duration_cast<chrono::milliseconds>(end - start).count();
    cout << "Word: " << pattern << " Duration (mili): " <<  dur << endl;
    cout << "Match: " << endl;
    print(match, text);

    return 0;
}