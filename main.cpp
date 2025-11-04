#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <bits/stdc++.h>
#include <fstream>

namespace py = pybind11;
using namespace std;

set<string> uniqueWords;
string text;
unordered_map<string, int> freq;

class TrieNode{
public:
    unordered_map<char, TrieNode*> children;
    bool isEndOfWord = false;
};

void read_file(const string& filename){
    ifstream file(filename);
    if (!file) return;

    uniqueWords.clear();
    text.assign((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
    file.close();
    string word;
    for(char ch : text){
        if(isalpha(static_cast<unsigned char>(ch))){
            word += static_cast<char>(tolower(ch));
        }
        else if(!word.empty()){
            uniqueWords.insert(word);
            freq[word]++;
            word.clear();
        }
    }
    if(!word.empty()){
        uniqueWords.insert(word);
        freq[word]++;
    }
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

vector<int> kmp_search(const string &pattern, const string &text){
    return kmp(pattern, text);
}

static TrieNode* root = nullptr;

TrieNode* newNode(){
    return new TrieNode();
}

void createTrie(){
    if(root == nullptr){
        root = newNode();
    }
    TrieNode* curr = root;
    for(auto word : uniqueWords){
        for(auto c : word){
            auto it  = curr->children.find(c);
            if(it == curr->children.end()){
                TrieNode* child = newNode();
                curr->children[c] = child;
                curr = child;
            }
            else{
                curr = it->second;
            }
        }
        curr->isEndOfWord = true;
        curr = root;
    }
}

void trie_collect(TrieNode* node, string &prefix, vector<string> &out){
    if(!node) return;
    if(node->isEndOfWord){
        out.push_back(prefix);
    }

    vector<char> keys;
    keys.reserve(node->children.size());
    for(auto &p : node->children) keys.push_back(p.first);
    sort(keys.begin(), keys.end());
    for(char k : keys){
        prefix.push_back(k);
        trie_collect(node->children[k], prefix, out);
        prefix.pop_back();
    }
}

vector<string> autocomplete(const string &prefix){
    vector<string> out;
    if(root == nullptr || prefix.empty()) return out;
    TrieNode* cur = root;
    for(auto c : prefix){
        auto it = cur->children.find(c);
        if(it == cur->children.end()) return out;
        cur = it->second;
    }
    string p = prefix;
    trie_collect(cur, p, out);

    sort(out.begin(), out.end(), [](const string &a, const string &b){
        int fa = freq.at(a);
        int fb = freq.at(b);
        if(fa != fb) return fa > fb;
        return a < b;
    });

    return out;
}

PYBIND11_MODULE(algorithms, m){
    m.doc() = "KMP search bindings";
    m.def("read_file", &read_file, "Read entire file into a string");
    m.def("kmp_search", &kmp_search, "Search pattern in text returning start indices");
    m.def("createTrie", &createTrie, "Create a trie from unique words");
    m.def("autocomplete", &autocomplete, py::arg("prefix"),
          "Return autocomplete suggestions for prefix");
}